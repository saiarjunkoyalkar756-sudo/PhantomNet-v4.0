"""Governed read-only analyst routes for attack-path analysis."""

from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query

from backend_api.attack_graph_engine.governed_attack_paths import (
    AttackPathQuery,
    GovernedAttackPathService,
    InMemoryTenantGraphStore,
    Neo4jTenantGraphStore,
)
from backend_api.case_management_service.workflow import CaseWorkflow
from backend_api.core.response import success_response
from backend_api.correlation_engine.alert_workflow import AlertWorkflow
from backend_api.correlation_engine.detection_store import DetectionRepository
from backend_api.endpoint_inventory_service.repository import EndpointInventoryRepository
from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User


router = APIRouter(prefix="/governed-attack-paths", tags=["Governed Attack Paths"])


def _configured_graph_service() -> GovernedAttackPathService:
    """Use Neo4j only when an operator explicitly selects it and supplies its environment secrets."""
    backend = os.getenv("PHANTOMNET_GRAPH_BACKEND", "memory").strip().lower()
    if backend == "neo4j":
        return GovernedAttackPathService(Neo4jTenantGraphStore())
    if backend != "memory":
        raise RuntimeError("PHANTOMNET_GRAPH_BACKEND must be either 'memory' or 'neo4j'.")
    return GovernedAttackPathService(InMemoryTenantGraphStore())


attack_path_service = _configured_graph_service()
detection_repository = DetectionRepository()
alert_workflow = AlertWorkflow()
endpoint_repository = EndpointInventoryRepository()
case_workflow = CaseWorkflow()


@router.post("/refresh")
async def refresh_tenant_graph(
    limit: int = Query(default=200, ge=1, le=500),
    current_user: User = Depends(require_capability("config:write")),
):
    """Project a bounded snapshot of authenticated-tenant evidence into the graph backend.

    This is a data-projection operation only. It does not execute playbooks, containment, agent
    commands, response adapters, or external enrichment.
    """
    tenant_id = str(current_user.tenant_id)
    projection = await attack_path_service.project_evidence(
        tenant_id,
        assets=await endpoint_repository.list_assets(tenant_id, limit=limit),
        integrity_observations=await endpoint_repository.list_integrity(tenant_id, limit=limit),
        detections=await detection_repository.list_for_tenant(tenant_id, limit=limit),
        alerts=await alert_workflow.list_for_tenant(tenant_id, limit=limit),
        cases=await case_workflow.list_cases(tenant_id, limit=limit),
    )
    return success_response(data=projection.model_dump(mode="json"))


@router.post("/analyze")
async def analyze_attack_path(
    query: AttackPathQuery,
    current_user: User = Depends(require_capability("alerts:read")),
):
    """Return a bounded, tenant-scoped, evidence-backed path analysis with no execution semantics."""
    try:
        analysis = await attack_path_service.analyze(str(current_user.tenant_id), query)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return success_response(data=analysis.model_dump(mode="json"))
