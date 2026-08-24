"""Regression coverage for deterministic event-stream advisory fallback behavior."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_STREAM_PROCESSOR = ROOT / "backend_api/shared/event_stream_processor.py"


def test_runtime_ai_fallback_does_not_generate_random_advisory_detections():
    source = EVENT_STREAM_PROCESSOR.read_text(encoding="utf-8")
    runtime_source = source.split("# Example Usage (for testing)", maxsplit=1)[0]

    assert "AI correlation plugin is unavailable" in runtime_source
    assert "Simulated AI Investigate" not in runtime_source
    assert "random.uniform(0.0, 0.4)" not in runtime_source
    assert "random.random() < 0.1" not in runtime_source
    assert "random.choice([\"anomaly\", \"signature\"])" not in runtime_source


def test_runtime_ai_fallback_retains_deterministic_rule_ti_and_ueba_paths():
    source = EVENT_STREAM_PROCESSOR.read_text(encoding="utf-8")

    assert "self._evaluate_correlation_rules" in source
    assert "self._check_threat_intelligence" in source
    assert 'detection_type = "ueba_anomaly"' in source
    assert "self.plugin_manager.execute_plugin_function" in source
