"""Source-contract regressions for the public portal user-route truthfulness boundary."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
USER_PORTAL_PAGE = ROOT / "phantomnet-website/app/user/page.tsx"


def test_user_portal_is_a_transparent_non_operational_boundary():
    source = USER_PORTAL_PAGE.read_text(encoding="utf-8")

    assert "User security portal is not operational" in source
    assert "does not display live endpoint posture" in source
    assert "governed service boundary" in source


def test_user_portal_does_not_reintroduce_simulated_security_operations_or_retired_clients():
    source = USER_PORTAL_PAGE.read_text(encoding="utf-8")

    for forbidden_marker in (
        "useState",
        "useEffect",
        "fetch(",
        "setInterval",
        "Math.random",
        "INITIAL_LOGS",
        "mock-user-token",
        "pn_tok_",
        "api/v1/vulnerability",
        "api/v1/honeypot",
        "audit-crypto-agility",
        "Kyber-1024",
        "Shor-vulnerable",
    ):
        assert forbidden_marker not in source
