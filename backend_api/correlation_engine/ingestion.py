"""Canonical normalized-event ingestion for the durable correlation data plane."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from backend_api.bas_engine.detection_pipeline import evaluate_normalized_baseline_event
from backend_api.correlation_engine.alert_workflow import AlertWorkflow, AlertWorkflowResult
from backend_api.correlation_engine.detection_store import DetectionRepository
from phantomnet_core.contracts import CONTRACT_VERSION, DetectionRecord, EventEnvelope


DetectionEvaluator = Callable[[Mapping[str, Any]], DetectionRecord | None]


@dataclass(frozen=True)
class BrokerIngestionResult:
    event: EventEnvelope
    persisted_detections: tuple[DetectionRecord, ...]
    created_detection_ids: tuple[str, ...]
    duplicate_detection_ids: tuple[str, ...]
    alert_workflows: tuple[AlertWorkflowResult, ...] = ()


class CanonicalBrokerProcessor:
    """Validate normalized broker messages and persist the detections they govern.

    Invalid envelopes deliberately raise errors so the resilient consumer retries and then
    routes persistent poison messages to its DLQ. Successful duplicate delivery is not an
    error: it returns the existing durable detection evidence without creating a second row.
    """

    def __init__(
        self,
        repository: DetectionRepository,
        evaluators: Sequence[DetectionEvaluator] = (evaluate_normalized_baseline_event,),
        alert_workflow: AlertWorkflow | None = None,
    ):
        self._repository = repository
        self._evaluators = tuple(evaluators)
        self._alert_workflow = alert_workflow

    async def process(self, message: Mapping[str, Any]) -> BrokerIngestionResult:
        event = EventEnvelope.model_validate(message)
        if event.schema_version != CONTRACT_VERSION:
            raise ValueError(
                f"Unsupported event schema version '{event.schema_version}'; expected '{CONTRACT_VERSION}'."
            )

        persisted: list[DetectionRecord] = []
        created_ids: list[str] = []
        duplicate_ids: list[str] = []
        alert_workflows: list[AlertWorkflowResult] = []
        normalized_message = dict(message)

        for evaluator in self._evaluators:
            detection = evaluator(normalized_message)
            if detection is None:
                continue
            self._validate_detection_binding(event, detection)
            stored_detection, created = await self._repository.persist(detection)
            persisted.append(stored_detection)
            if created:
                created_ids.append(stored_detection.detection_id)
            else:
                duplicate_ids.append(stored_detection.detection_id)
            if self._alert_workflow is not None:
                # AlertWorkflow treats an already-linked detection as a transport duplicate.
                # Calling it on replay repairs a failed post-detection workflow without new alerts.
                alert_workflows.append(await self._alert_workflow.ingest_detection(stored_detection))

        return BrokerIngestionResult(
            event=event,
            persisted_detections=tuple(persisted),
            created_detection_ids=tuple(created_ids),
            duplicate_detection_ids=tuple(duplicate_ids),
            alert_workflows=tuple(alert_workflows),
        )

    @staticmethod
    def _validate_detection_binding(event: EventEnvelope, detection: DetectionRecord) -> None:
        if detection.event_id != event.event_id:
            raise ValueError("Detection event_id does not match the canonical broker event.")
        if detection.tenant_id != event.tenant_id:
            raise ValueError("Detection tenant_id does not match the canonical broker event.")
        if detection.correlation_id != event.correlation_id:
            raise ValueError("Detection correlation_id does not match the canonical broker event.")
