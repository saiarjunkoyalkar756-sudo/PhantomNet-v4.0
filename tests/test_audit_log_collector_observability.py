from __future__ import annotations

import ast
import sys
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from backend_api.audit_log_collector import main as audit_main
from backend_api.audit_log_collector.main import AuditLogCreate


ROOT = Path(__file__).resolve().parents[1]
AUDIT_COLLECTOR_PATH = ROOT / "backend_api/audit_log_collector/main.py"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"


def _audit_factory_dependencies() -> tuple[str, ...]:
    module = ast.parse(AUDIT_COLLECTOR_PATH.read_text(encoding="utf-8"), filename=str(AUDIT_COLLECTOR_PATH))
    calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "create_phantom_service"
    ]
    assert len(calls) == 1
    keywords = {keyword.arg: keyword.value for keyword in calls[0].keywords if keyword.arg}
    return ast.literal_eval(keywords["required_dependencies"])


def _alert_audit_record() -> AuditLogCreate:
    return AuditLogCreate(
        raw_log_data="controlled audit mirror fixture",
        action="alert_created",
        event_id="audit-fixture-001",
        metadata={"severity": "high"},
    )


def test_audit_log_collector_declares_database_only_as_required_readiness_dependency():
    assert _audit_factory_dependencies() == ("database",)
    assert audit_main.app.state.required_dependencies == ("database",)


def test_audit_log_collector_compose_healthcheck_uses_dependency_aware_ready_route():
    compose = yaml.safe_load(ROOT_COMPOSE_PATH.read_text(encoding="utf-8"))
    healthcheck = compose["services"]["audit-log-collector"]["healthcheck"]

    assert healthcheck["test"][0] == "CMD-SHELL"
    assert "/ready" in healthcheck["test"][1]
    assert healthcheck["timeout"] == "5s"
    assert healthcheck["retries"] == 3


@pytest.mark.asyncio
async def test_audit_log_collector_startup_initializes_collector_owned_schema(monkeypatch):
    initialized: list[bool] = []
    monkeypatch.setattr(audit_main, "initialize_database", lambda: initialized.append(True))

    await audit_main.audit_log_collector_startup(audit_main.app)

    assert initialized == [True]


@pytest.mark.asyncio
async def test_missing_optional_ledger_does_not_block_persisted_audit_flow(monkeypatch):
    monkeypatch.delitem(sys.modules, "blockchain_layer", raising=False)
    monkeypatch.delitem(sys.modules, "blockchain_layer.blockchain_client", raising=False)

    await audit_main._mirror_alert_to_optional_ledger(_alert_audit_record())


@pytest.mark.asyncio
async def test_optional_ledger_failure_is_logged_not_silently_swallowed(monkeypatch):
    package = ModuleType("blockchain_layer")
    package.__path__ = []  # type: ignore[attr-defined]
    client = ModuleType("blockchain_layer.blockchain_client")

    async def failing_submit(**_kwargs):
        raise RuntimeError("controlled optional mirror failure")

    client.submit_alert_to_ledger = failing_submit  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "blockchain_layer", package)
    monkeypatch.setitem(sys.modules, "blockchain_layer.blockchain_client", client)
    logged: list[str] = []
    monkeypatch.setattr(audit_main.logger, "exception", lambda message: logged.append(message))

    await audit_main._mirror_alert_to_optional_ledger(_alert_audit_record())

    assert logged == ["Optional audit ledger mirror failed after durable audit persistence."]
