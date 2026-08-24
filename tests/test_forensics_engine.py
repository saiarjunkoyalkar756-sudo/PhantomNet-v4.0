from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend_api.forensics_engine.main import app


ROOT = Path(__file__).resolve().parents[1]
FORENSICS_DOCKERFILE = ROOT / "backend_api/forensics_engine/Dockerfile"
ROOT_COMPOSE_PATH = ROOT / "docker-compose.yml"

client = TestClient(app)


def test_legacy_forensics_has_no_container_or_compose_surface():
    assert not FORENSICS_DOCKERFILE.exists()
    assert "forensics-engine:" not in ROOT_COMPOSE_PATH.read_text(encoding="utf-8")


def test_legacy_forensics_timeline_route_is_retired_for_source_filter_payloads():
    response = client.post(
        "/timeline/build/",
        json={"asset_id": "test-asset", "data_sources": ["logs"]},
    )

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_FORENSICS_API_RETIRED"


def test_legacy_forensics_timeline_route_is_retired_for_multi_source_payloads():
    response = client.post(
        "/timeline/build/",
        json={"asset_id": "test-asset", "data_sources": ["logs", "disk_image"]},
    )

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_FORENSICS_API_RETIRED"


def test_legacy_forensics_timeline_route_is_retired_for_time_range_payloads():
    response = client.post(
        "/timeline/build/",
        json={
            "asset_id": "test-asset",
            "start_time": "2026-05-28T05:15:00+00:00",
            "data_sources": ["logs", "disk_image"],
        },
    )

    assert response.status_code == 410
    assert json.loads(response.content)["error"]["code"] == "LEGACY_FORENSICS_API_RETIRED"
