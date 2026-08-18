"""Tenant-scoped, structured threat hunting and SOC dashboard aggregation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend_api.shared.database import (
    AnalystAlertRow,
    AsyncSessionLocal,
    DetectionRecordRow,
    InvestigationCaseRow,
    SavedHuntRow,
    engine,
)


SessionFactory = Callable[[], AsyncSession]
MAX_HUNT_RESULTS = 200
HUNT_DATASETS = {"detections", "alerts", "cases"}


class HuntFilter(BaseModel):
    field: str = Field(min_length=1, max_length=64)
    operator: Literal["eq", "in", "contains"] = "eq"
    value: str | list[str] = Field(...)

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str | list[str]) -> str | list[str]:
        values = [value] if isinstance(value, str) else value
        if not values or len(values) > 25 or any(not str(item) or len(str(item)) > 128 for item in values):
            raise ValueError("Hunt filter values must contain between 1 and 25 bounded non-empty values.")
        return value


class HuntRequest(BaseModel):
    dataset: Literal["detections", "alerts", "cases"]
    filters: list[HuntFilter] = Field(default_factory=list, max_length=10)
    limit: int = Field(default=100, ge=1, le=MAX_HUNT_RESULTS)


class SavedHuntCreate(HuntRequest):
    name: str = Field(min_length=3, max_length=80)
    description: str | None = Field(default=None, max_length=240)


class SavedHunt(BaseModel):
    hunt_id: str
    name: str
    description: str | None
    dataset: str
    filters: list[HuntFilter]
    created_by: str
    created_at: datetime
    updated_at: datetime


AUTOMATED_HUNT_TEMPLATES: dict[str, HuntRequest] = {
    "high-severity-unresolved": HuntRequest(
        dataset="alerts",
        filters=[
            HuntFilter(field="severity", operator="in", value=["high", "critical"]),
            HuntFilter(field="status", operator="in", value=["new", "triaged", "in_progress"]),
        ],
    ),
    "command-and-control-mitre": HuntRequest(
        dataset="detections",
        filters=[HuntFilter(field="mitre_technique", operator="in", value=["T1071.001", "T1071.004"])],
    ),
}


FIELD_MAP = {
    "detections": {
        "severity": DetectionRecordRow.severity,
        "status": DetectionRecordRow.status,
        "rule_id": DetectionRecordRow.rule_id,
        "correlation_id": DetectionRecordRow.correlation_id,
        "event_id": DetectionRecordRow.event_id,
        "title": DetectionRecordRow.title,
    },
    "alerts": {
        "severity": AnalystAlertRow.severity,
        "status": AnalystAlertRow.status,
        "correlation_id": AnalystAlertRow.correlation_id,
        "case_id": AnalystAlertRow.case_id,
        "title": AnalystAlertRow.title,
    },
    "cases": {
        "severity": InvestigationCaseRow.severity,
        "status": InvestigationCaseRow.status,
        "created_by": InvestigationCaseRow.created_by,
        "assigned_to": InvestigationCaseRow.assigned_to,
        "title": InvestigationCaseRow.title,
    },
}


def _utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat()


def _detection_result(row: DetectionRecordRow) -> dict[str, Any]:
    return {
        "record_type": "detection",
        "detection_id": row.detection_id,
        "event_id": row.event_id,
        "rule_id": row.rule_id,
        "rule_version": row.rule_version,
        "correlation_id": row.correlation_id,
        "severity": row.severity,
        "status": row.status,
        "title": row.title,
        "timestamp": _utc(row.detected_at),
        "mitre_evidence": list(row.mitre_evidence),
        "tags": list(row.tags),
        "evidence": dict(row.evidence),
    }


def _alert_result(row: AnalystAlertRow) -> dict[str, Any]:
    return {
        "record_type": "alert",
        "alert_id": row.alert_id,
        "detection_ids": list(row.detection_ids),
        "correlation_id": row.correlation_id,
        "severity": row.severity,
        "status": row.status,
        "title": row.title,
        "timestamp": _utc(row.last_seen),
        "occurrence_count": row.occurrence_count,
        "case_id": row.case_id,
        "mitre_evidence": list(row.mitre_evidence),
        "evidence": dict(row.evidence),
    }


def _case_result(row: InvestigationCaseRow) -> dict[str, Any]:
    return {
        "record_type": "case",
        "case_id": row.case_id,
        "alert_ids": list(row.alert_ids),
        "severity": row.severity,
        "status": row.status,
        "title": row.title,
        "timestamp": _utc(row.updated_at),
        "created_by": row.created_by,
        "assigned_to": row.assigned_to,
        "evidence": dict(row.evidence),
    }


async def init_hunt_store() -> None:
    """Create saved-hunt storage when migrations have not already provisioned it."""
    async with engine.begin() as connection:
        await connection.run_sync(SavedHuntRow.__table__.create, checkfirst=True)


class ThreatHuntingService:
    """Read-only governed hunt engine over canonical tenant-owned SOC records."""

    def __init__(self, session_factory: SessionFactory = AsyncSessionLocal):
        self._session_factory = session_factory

    @staticmethod
    def _validate_filters(request: HuntRequest) -> None:
        allowed = FIELD_MAP[request.dataset]
        for filter_item in request.filters:
            if filter_item.field == "mitre_technique" and request.dataset == "detections":
                if filter_item.operator not in {"eq", "in"}:
                    raise ValueError("mitre_technique supports only eq or in operators.")
                continue
            if filter_item.field not in allowed:
                raise ValueError(f"Field '{filter_item.field}' cannot be searched in {request.dataset}.")
            if filter_item.operator == "contains" and filter_item.field not in {"title"}:
                raise ValueError("contains is limited to the title field.")

    @staticmethod
    def _apply_sql_filters(statement: Any, request: HuntRequest) -> tuple[Any, list[HuntFilter]]:
        post_filters: list[HuntFilter] = []
        for filter_item in request.filters:
            if filter_item.field == "mitre_technique":
                post_filters.append(filter_item)
                continue
            column = FIELD_MAP[request.dataset][filter_item.field]
            values = [filter_item.value] if isinstance(filter_item.value, str) else filter_item.value
            if filter_item.operator == "eq":
                statement = statement.where(column == values[0])
            elif filter_item.operator == "in":
                statement = statement.where(column.in_(values))
            else:
                statement = statement.where(column.ilike(f"%{values[0]}%"))
        return statement, post_filters

    @staticmethod
    def _matches_post_filters(record: Mapping[str, Any], filters: Sequence[HuntFilter]) -> bool:
        techniques = {
            str(item.get("technique_id"))
            for item in record.get("mitre_evidence", [])
            if isinstance(item, Mapping) and item.get("technique_id")
        }
        for filter_item in filters:
            values = {filter_item.value} if isinstance(filter_item.value, str) else set(filter_item.value)
            if filter_item.field == "mitre_technique" and not techniques.intersection(values):
                return False
        return True

    async def hunt(self, tenant_id: str, request: HuntRequest) -> dict[str, Any]:
        self._validate_filters(request)
        model = {
            "detections": DetectionRecordRow,
            "alerts": AnalystAlertRow,
            "cases": InvestigationCaseRow,
        }[request.dataset]
        serializer = {
            "detections": _detection_result,
            "alerts": _alert_result,
            "cases": _case_result,
        }[request.dataset]
        order_column = {
            "detections": DetectionRecordRow.detected_at,
            "alerts": AnalystAlertRow.last_seen,
            "cases": InvestigationCaseRow.updated_at,
        }[request.dataset]

        statement = select(model).where(model.tenant_id == UUID(tenant_id)).order_by(order_column.desc())
        statement, post_filters = self._apply_sql_filters(statement, request)
        # Fetch a bounded superset because MITRE evidence is portable JSON filtered in process.
        async with self._session_factory() as session:
            rows = await session.scalars(statement.limit(MAX_HUNT_RESULTS))
            records = [serializer(row) for row in rows]
        records = [record for record in records if self._matches_post_filters(record, post_filters)]
        return {
            "dataset": request.dataset,
            "filters": [filter_item.model_dump() for filter_item in request.filters],
            "result_count": len(records[: request.limit]),
            "results": records[: request.limit],
            "automated_actions": [],
            "note": "Hunts are read-only and do not dispatch containment or response actions.",
        }

    async def create_saved_hunt(self, tenant_id: str, actor: str, request: SavedHuntCreate) -> SavedHunt:
        self._validate_filters(request)
        now = datetime.now(timezone.utc)
        saved = SavedHunt(
            hunt_id=str(uuid4()),
            name=request.name,
            description=request.description,
            dataset=request.dataset,
            filters=request.filters,
            created_by=actor,
            created_at=now,
            updated_at=now,
        )
        async with self._session_factory() as session:
            row = SavedHuntRow(
                hunt_id=saved.hunt_id,
                tenant_id=UUID(tenant_id),
                name=saved.name,
                description=saved.description,
                dataset=saved.dataset,
                filters=[item.model_dump() for item in saved.filters],
                created_by=saved.created_by,
                created_at=saved.created_at,
                updated_at=saved.updated_at,
            )
            session.add(row)
            await session.commit()
        return saved

    async def list_saved_hunts(self, tenant_id: str) -> list[SavedHunt]:
        async with self._session_factory() as session:
            rows = await session.scalars(
                select(SavedHuntRow)
                .where(SavedHuntRow.tenant_id == UUID(tenant_id))
                .order_by(SavedHuntRow.updated_at.desc())
            )
            return [
                SavedHunt(
                    hunt_id=row.hunt_id,
                    name=row.name,
                    description=row.description,
                    dataset=row.dataset,
                    filters=[HuntFilter.model_validate(item) for item in row.filters],
                    created_by=row.created_by,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
                for row in rows
            ]

    async def run_saved_hunt(self, tenant_id: str, hunt_id: str) -> dict[str, Any]:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(SavedHuntRow).where(SavedHuntRow.tenant_id == UUID(tenant_id), SavedHuntRow.hunt_id == hunt_id)
            )
            if row is None:
                raise LookupError("Saved hunt was not found for the authenticated tenant.")
            request = HuntRequest(dataset=row.dataset, filters=[HuntFilter.model_validate(item) for item in row.filters])
        return await self.hunt(tenant_id, request)

    async def automated_hunts(self, tenant_id: str) -> dict[str, dict[str, Any]]:
        return {name: await self.hunt(tenant_id, request) for name, request in AUTOMATED_HUNT_TEMPLATES.items()}

    async def dashboard_summary(self, tenant_id: str) -> dict[str, Any]:
        detection_data = await self.hunt(tenant_id, HuntRequest(dataset="detections", limit=MAX_HUNT_RESULTS))
        alert_data = await self.hunt(tenant_id, HuntRequest(dataset="alerts", limit=MAX_HUNT_RESULTS))
        case_data = await self.hunt(tenant_id, HuntRequest(dataset="cases", limit=MAX_HUNT_RESULTS))
        detections = detection_data["results"]
        alerts = alert_data["results"]
        cases = case_data["results"]
        severity_counts = Counter(item["severity"] for item in alerts)
        status_counts = Counter(item["status"] for item in alerts)
        mitre_counts = Counter(
            evidence["technique_id"]
            for detection in detections
            for evidence in detection.get("mitre_evidence", [])
            if isinstance(evidence, Mapping) and evidence.get("technique_id")
        )
        open_case_statuses = {"new", "triaged", "in_progress"}
        return {
            "metrics": {
                "detections": len(detections),
                "active_alerts": sum(status_counts[status] for status in ("new", "triaged", "in_progress")),
                "critical_alerts": severity_counts["critical"],
                "open_cases": sum(1 for case in cases if case["status"] in open_case_statuses),
            },
            "alerts_by_severity": [
                {"severity": severity, "count": severity_counts[severity]}
                for severity in ("critical", "high", "medium", "low", "informational")
            ],
            "alerts_by_status": [{"status": status, "count": count} for status, count in sorted(status_counts.items())],
            "top_mitre_techniques": [
                {"technique_id": technique_id, "count": count}
                for technique_id, count in mitre_counts.most_common(10)
            ],
            "recent_alerts": alerts[:10],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
