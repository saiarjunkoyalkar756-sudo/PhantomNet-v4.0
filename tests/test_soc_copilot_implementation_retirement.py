"""Source-contract regression for retired fabricated SOC copilot implementation."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COPILOT_IMPLEMENTATION = ROOT / "backend_api/soc_copilot_service/soc_copilot_service.py"
COPILOT_MAIN = ROOT / "backend_api/soc_copilot_service/main.py"
COPILOT_APP = ROOT / "backend_api/soc_copilot_service/app.py"


def test_fabricated_soc_copilot_implementation_remains_absent():
    assert not COPILOT_IMPLEMENTATION.exists()


def test_retained_soc_copilot_boundary_remains_fail_closed():
    source = COPILOT_MAIN.read_text(encoding="utf-8") + COPILOT_APP.read_text(encoding="utf-8")

    assert "LEGACY_SOC_COPILOT_API_RETIRED" in source
    assert "status_code=410" in source
    assert "SOCCopilotService" not in source
