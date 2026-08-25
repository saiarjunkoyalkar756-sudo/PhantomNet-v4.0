"""Regression coverage for deterministic fail-closed zero-trust evaluation."""
from __future__ import annotations

import pytest

from backend_api.shared.zero_trust_engine import Identity, ZeroTrustEngine


@pytest.mark.asyncio
async def test_missing_trust_evidence_is_deterministic_and_fails_closed():
    engine = ZeroTrustEngine()

    score = await engine._evaluate_trust_score(Identity(id="user-a", type="user"))

    assert score.score == 0.0
    assert score.factors == {"reason": "required_trust_evidence_unavailable"}
    assert await engine.get_trust_score("unknown-user") is None


@pytest.mark.asyncio
async def test_complete_bounded_trust_evidence_produces_deterministic_score():
    engine = ZeroTrustEngine()
    identity = Identity(
        id="user-b",
        type="user",
        attributes={
            "login_history_score": 90,
            "device_health_score": 80,
            "geo_location_score": 70,
        },
    )

    first = await engine._evaluate_trust_score(identity)
    second = await engine._evaluate_trust_score(identity)

    assert first.score == 80.0
    assert second.score == first.score
    assert second.factors == first.factors


def test_engine_has_no_randomized_trust_or_device_posture_fallback():
    source = __import__("pathlib").Path(__file__).resolve().parents[1].joinpath(
        "backend_api/shared/zero_trust_engine.py"
    ).read_text(encoding="utf-8")

    assert "random." not in source
    assert "required_trust_evidence_unavailable" in source
    assert 'context.setdefault("device_health", "unknown")' in source
