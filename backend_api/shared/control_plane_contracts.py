"""Source-controlled observability contracts for the Phase 7 self-hosted reference.

This inventory is intentionally limited to `deploy/self-hosted/docker-compose.yml`. It does not
claim observability coverage for the broad legacy development Compose topology. Application routes
use secret-safe HTTP diagnostics; infrastructure components use their configured container
healthchecks or native control-plane probes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


STANDARD_APPLICATION_ENDPOINTS = ("/health", "/ready", "/metrics")
GATEWAY_REQUIRED_DEPENDENCIES = ("database", "kafka", "redis", "neo4j")


@dataclass(frozen=True)
class ControlPlaneObservabilityContract:
    """One non-secret health/readiness/metrics contract for the self-hosted reference topology."""

    service_name: str
    component_kind: Literal["application", "infrastructure", "observability"]
    health_probe: str
    readiness_probe: str
    metrics_endpoint: str | None
    depends_on: tuple[str, ...] = ()
    notes: str = ""

    @property
    def is_http_application(self) -> bool:
        return self.component_kind == "application"


def _validate_contract(contract: ControlPlaneObservabilityContract) -> None:
    if not contract.service_name:
        raise ValueError("Control-plane contracts require a service_name.")
    if contract.component_kind == "application":
        if (
            contract.health_probe != "/health"
            or contract.readiness_probe != "/ready"
            or contract.metrics_endpoint != "/metrics"
        ):
            raise ValueError("Application contracts must use the standardized health, readiness, and metrics endpoints.")
    if contract.component_kind != "application" and contract.metrics_endpoint is not None:
        if not contract.metrics_endpoint.startswith("/"):
            raise ValueError("HTTP metrics endpoints must begin with '/'.")


PHASE7_CONTROL_PLANE_CONTRACTS = (
    ControlPlaneObservabilityContract(
        service_name="postgres",
        component_kind="infrastructure",
        health_probe="pg_isready",
        readiness_probe="compose service_healthy",
        metrics_endpoint=None,
        notes="PostgreSQL is internal-only; its container healthcheck is the self-hosted readiness source.",
    ),
    ControlPlaneObservabilityContract(
        service_name="redis",
        component_kind="infrastructure",
        health_probe="redis-cli ping",
        readiness_probe="compose service_healthy",
        metrics_endpoint=None,
        notes="Redis is internal-only and password-protected; readiness never emits its URL or credentials.",
    ),
    ControlPlaneObservabilityContract(
        service_name="redpanda",
        component_kind="infrastructure",
        health_probe="rpk cluster health",
        readiness_probe="compose service_healthy",
        metrics_endpoint=None,
        notes="Redpanda is the Kafka-compatible internal broker dependency.",
    ),
    ControlPlaneObservabilityContract(
        service_name="neo4j",
        component_kind="infrastructure",
        health_probe="HTTP localhost:7474 probe",
        readiness_probe="compose service_healthy",
        metrics_endpoint=None,
        notes="Neo4j is internal-only; the gateway readiness probe verifies Bolt reachability.",
    ),
    ControlPlaneObservabilityContract(
        service_name="gateway-service",
        component_kind="application",
        health_probe="/health",
        readiness_probe="/ready",
        metrics_endpoint="/metrics",
        depends_on=("postgres", "redis", "redpanda", "neo4j"),
        notes="Gateway readiness maps postgres, redis, redpanda, and neo4j to fail-closed application dependencies.",
    ),
    ControlPlaneObservabilityContract(
        service_name="prometheus",
        component_kind="observability",
        health_probe="/-/healthy",
        readiness_probe="/-/ready",
        metrics_endpoint="/metrics",
        depends_on=("gateway-service",),
        notes="Prometheus is loopback-exposed and scrapes the gateway only on the internal observability network.",
    ),
)


for _contract in PHASE7_CONTROL_PLANE_CONTRACTS:
    _validate_contract(_contract)


PHASE7_CONTRACTS_BY_SERVICE = {contract.service_name: contract for contract in PHASE7_CONTROL_PLANE_CONTRACTS}
if len(PHASE7_CONTRACTS_BY_SERVICE) != len(PHASE7_CONTROL_PLANE_CONTRACTS):
    raise RuntimeError("Phase 7 control-plane observability service names must be unique.")


def phase7_contract(service_name: str) -> ControlPlaneObservabilityContract:
    """Return a declared Phase 7 observability contract or fail explicitly for unknown services."""
    try:
        return PHASE7_CONTRACTS_BY_SERVICE[service_name]
    except KeyError as exc:
        raise LookupError(f"No Phase 7 control-plane observability contract is declared for {service_name!r}.") from exc
