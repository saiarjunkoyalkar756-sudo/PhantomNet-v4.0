from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from backend_api.shared.service_factory import create_phantom_service
from backend_api.threat_intelligence_service import main as threat_main


ROOT = Path(__file__).resolve().parents[1]
THREAT_INTELLIGENCE_DOCKERFILE = ROOT / "backend_api/threat_intelligence_service/Dockerfile"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"


class _Result:
    def __init__(self, raw_responses: dict[str, object]):
        self.raw_responses = raw_responses

    def model_dump(self, mode: str = "python") -> dict[str, object]:
        return {
            "indicator": {"value": "198.51.100.10", "type": "ip"},
            "is_malicious": False,
            "overall_threat_score": 0,
            "raw_responses": self.raw_responses,
        }


def test_explicit_empty_dependencies_do_not_inherit_generic_service_dependencies():
    app = create_phantom_service("Advisory Service", "Optional upstreams", required_dependencies=())

    assert app.state.required_dependencies == ()
    assert threat_main.app.state.required_dependencies == ()


def test_threat_intelligence_container_and_compose_healthcheck_target_the_real_service():
    assert '"main:app"' in THREAT_INTELLIGENCE_DOCKERFILE.read_text(encoding="utf-8")

    compose = yaml.safe_load(ROOT_COMPOSE_PATH.read_text(encoding="utf-8"))
    healthcheck = compose["services"]["threat-intelligence-service"]["healthcheck"]
    assert healthcheck["test"][0] == "CMD-SHELL"
    assert "/ready" in healthcheck["test"][1]
    assert healthcheck["timeout"] == "5s"
    assert healthcheck["retries"] == 3


def test_threat_intelligence_routes_require_existing_alerts_read_capability():
    guarded_routes = {
        route.path: route
        for route in threat_main.app.routes
        if getattr(route, "path", "") in {"/api/threat-intel/lookup", "/api/threat-intel/bulk"}
    }

    assert set(guarded_routes) == {"/api/threat-intel/lookup", "/api/threat-intel/bulk"}
    for route in guarded_routes.values():
        assert route.dependant.dependencies


@pytest.mark.asyncio
async def test_lookup_hides_provider_payloads_but_retains_provider_availability(monkeypatch):
    async def fake_enrich(_value: str, _type: str) -> _Result:
        return _Result({"virustotal": {"api_key": "never-return"}, "misp": {"error": "provider down"}})

    monkeypatch.setattr(threat_main.threat_enricher, "enrich_indicator", fake_enrich)
    response = await threat_main.lookup_indicator(
        threat_main.IndicatorLookup(value="198.51.100.10", type="ip"),
        current_user=SimpleNamespace(),
    )

    assert response["success"] is True
    assert response["data"]["provider_status"] == {"virustotal": "available", "misp": "unavailable"}
    assert "raw_responses" not in response["data"]
    assert "never-return" not in json.dumps(response)


@pytest.mark.asyncio
async def test_lookup_returns_generic_unavailable_error_without_provider_exception_text(monkeypatch):
    async def failing_enrich(_value: str, _type: str) -> _Result:
        raise RuntimeError("upstream credential alpha-secret was rejected")

    monkeypatch.setattr(threat_main.threat_enricher, "enrich_indicator", failing_enrich)
    response = await threat_main.lookup_indicator(
        threat_main.IndicatorLookup(value="198.51.100.10", type="ip"),
        current_user=SimpleNamespace(),
    )

    payload = json.loads(response.body)
    assert response.status_code == 503
    assert payload["error"]["code"] == "ENRICHMENT_UNAVAILABLE"
    assert "alpha-secret" not in json.dumps(payload)


@pytest.mark.asyncio
async def test_bulk_lookup_retains_per_indicator_failure_without_serializing_exception(monkeypatch):
    async def selectively_failing_enrich(value: str, _type: str) -> _Result:
        if value == "203.0.113.2":
            raise RuntimeError("provider exception with sensitive diagnostic")
        return _Result({"virustotal": {"attributes": {}}})

    monkeypatch.setattr(threat_main.threat_enricher, "enrich_indicator", selectively_failing_enrich)
    response = await threat_main.bulk_lookup_indicators(
        [
            threat_main.IndicatorLookup(value="198.51.100.10", type="ip"),
            threat_main.IndicatorLookup(value="203.0.113.2", type="ip"),
        ],
        current_user=SimpleNamespace(),
    )

    assert response["success"] is True
    assert response["data"][0]["result"]["provider_status"] == {"virustotal": "available"}
    assert response["data"][1]["error"]["code"] == "ENRICHMENT_UNAVAILABLE"
    assert "sensitive diagnostic" not in json.dumps(response)


@pytest.mark.asyncio
async def test_optional_cache_probe_does_not_block_advisory_service_startup(monkeypatch):
    async def failing_ping() -> None:
        raise ConnectionError("controlled cache outage")

    monkeypatch.setattr(threat_main.threat_intel_cache, "client", object())
    monkeypatch.setattr(threat_main.threat_intel_cache, "ping", failing_ping)

    await threat_main.ti_startup(threat_main.app)
