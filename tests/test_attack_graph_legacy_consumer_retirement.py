"""Source-contract regressions for retired unscoped attack-graph consumption."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATTACK_GRAPH_DIR = ROOT / "backend_api/attack_graph_engine"
ATTACK_GRAPH_MAIN = ATTACK_GRAPH_DIR / "main.py"
ENV_EXAMPLE = ROOT / "backend_api/.env.example"
GOVERNED_API = ATTACK_GRAPH_DIR / "governed_api.py"


def test_unscoped_attack_graph_consumer_modules_and_enablement_setting_remain_absent():
    assert not (ATTACK_GRAPH_DIR / "event_consumer.py").exists()
    assert not (ATTACK_GRAPH_DIR / "graph_builder.py").exists()
    assert not (ATTACK_GRAPH_DIR / "path_analyzer.py").exists()
    assert "PHANTOMNET_LEGACY_ATTACK_GRAPH_ENABLED" not in ENV_EXAMPLE.read_text(encoding="utf-8")


def test_attack_graph_entrypoint_is_governed_only_and_legacy_traversal_is_explicitly_retired():
    source = ATTACK_GRAPH_MAIN.read_text(encoding="utf-8")
    governed_source = GOVERNED_API.read_text(encoding="utf-8")

    assert "LEGACY_UNSCOPED_ATTACK_GRAPH_RETIRED" in source
    assert "status_code=410" in source
    assert "consume_events" not in source
    assert "GraphBuilder" not in source
    assert "PathAnalyzer" not in source
    assert "PHANTOMNET_LEGACY_ATTACK_GRAPH_ENABLED" not in source
    assert "app.include_router(governed_attack_path_router, prefix=\"/api\")" in source
    assert 'require_capability("config:write")' in governed_source
    assert 'require_capability("alerts:read")' in governed_source
    assert "current_user.tenant_id" in governed_source
