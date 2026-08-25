"""Source-contract regression for retired neural-security-language parser."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NSL_PACKAGE = ROOT / "features/neural_security_language"
PNQL_APP = ROOT / "backend_api/pnql_engine/app.py"


def test_neural_security_language_parser_package_remains_absent():
    assert not NSL_PACKAGE.exists()


def test_retired_pnql_boundary_remains_explicit():
    source = PNQL_APP.read_text(encoding="utf-8")

    assert 'code="LEGACY_PNQL_API_RETIRED"' in source
    assert "Use governed tenant-scoped analytical workflows." in source
