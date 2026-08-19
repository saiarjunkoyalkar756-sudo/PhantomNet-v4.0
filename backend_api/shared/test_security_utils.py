from datetime import datetime, timedelta, timezone
import uuid

import jwt
import pytest
from fastapi import HTTPException

from backend_api.shared.jti_store import InMemoryJtiStore
from backend_api.shared.security_utils import (
    create_inter_node_jwt,
    generate_key_pair,
    verify_inter_node_jwt,
)


@pytest.fixture
def jti_store() -> InMemoryJtiStore:
    """Give each security test an isolated replay-protection store."""
    return InMemoryJtiStore()


def test_create_and_verify_jwt(jti_store: InMemoryJtiStore):
    private_key, public_key = generate_key_pair()
    token = create_inter_node_jwt(1, "test_cluster", "agent:heartbeat", private_key)

    decoded_payload = verify_inter_node_jwt(token, public_key, "test_cluster", jti_store=jti_store)

    assert decoded_payload["iss"] == "1"
    assert decoded_payload["sub"] == "1"
    assert decoded_payload["aud"] == "test_cluster"
    assert decoded_payload["scope"] == "agent:heartbeat"
    assert decoded_payload["jti"]


def test_verify_jwt_rejects_bad_signature(jti_store: InMemoryJtiStore):
    private_key, _ = generate_key_pair()
    _, wrong_public_key = generate_key_pair()
    token = create_inter_node_jwt(1, "test_cluster", "agent:heartbeat", private_key)

    with pytest.raises(HTTPException, match="Invalid JWT"):
        verify_inter_node_jwt(token, wrong_public_key, "test_cluster", jti_store=jti_store)


def test_verify_jwt_rejects_wrong_audience(jti_store: InMemoryJtiStore):
    private_key, public_key = generate_key_pair()
    token = create_inter_node_jwt(1, "test_cluster", "agent:heartbeat", private_key)

    with pytest.raises(HTTPException, match="Invalid audience"):
        verify_inter_node_jwt(token, public_key, "wrong_cluster", jti_store=jti_store)


def test_verify_jwt_rejects_expired_token(jti_store: InMemoryJtiStore):
    private_key, public_key = generate_key_pair()
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {
            "iss": "1",
            "sub": "1",
            "aud": "test_cluster",
            "iat": now - timedelta(minutes=5),
            "exp": now - timedelta(minutes=1),
            "jti": str(uuid.uuid4()),
            "scope": "agent:heartbeat",
        },
        private_key,
        algorithm="RS256",
    )

    with pytest.raises(HTTPException, match="JWT has expired"):
        verify_inter_node_jwt(expired_token, public_key, "test_cluster", jti_store=jti_store)


def test_verify_jwt_rejects_reused_jti(jti_store: InMemoryJtiStore):
    private_key, public_key = generate_key_pair()
    token = create_inter_node_jwt(1, "test_cluster", "agent:heartbeat", private_key)

    verify_inter_node_jwt(token, public_key, "test_cluster", jti_store=jti_store)

    with pytest.raises(HTTPException, match="has been used already"):
        verify_inter_node_jwt(token, public_key, "test_cluster", jti_store=jti_store)
