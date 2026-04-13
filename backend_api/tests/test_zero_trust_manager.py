import pytest
from fastapi import Request, HTTPException
from backend_api.security.zero_trust_manager import ZeroTrustManager

@pytest.fixture
def zero_trust_manager():
    return ZeroTrustManager()

@pytest.mark.asyncio
async def test_verify_request_success(zero_trust_manager):
    request = Request({
        "type": "http",
        "headers": {
            "client-cert-fingerprint": "test-fingerprint",
            "Authorization": "Bearer valid-token",
            "X-Device-Health": "ok"
        },
        "client": ("127.0.0.1", 12345)
    })
    payload = await zero_trust_manager.verify_request(request)
    assert payload == {"user_id": "user-123", "roles": ["user"]}

@pytest.mark.asyncio
async def test_verify_request_no_mtls(zero_trust_manager):
    request = Request({
        "type": "http",
        "headers": {
            "Authorization": "Bearer valid-token",
            "X-Device-Health": "ok"
        },
        "client": ("127.0.0.1", 12345)
    })
    with pytest.raises(HTTPException) as excinfo:
        await zero_trust_manager.verify_request(request)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "mTLS verification failed"

@pytest.mark.asyncio
async def test_verify_request_invalid_jwt(zero_trust_manager):
    request = Request({
        "type": "http",
        "headers": {
            "client-cert-fingerprint": "test-fingerprint",
            "Authorization": "Bearer invalid-token",
            "X-Device-Health": "ok"
        },
        "client": ("127.0.0.1", 12345)
    })
    with pytest.raises(HTTPException) as excinfo:
        await zero_trust_manager.verify_request(request)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid JWT"

@pytest.mark.asyncio
async def test_verify_request_bad_posture(zero_trust_manager):
    request = Request({
        "type": "http",
        "headers": {
            "client-cert-fingerprint": "test-fingerprint",
            "Authorization": "Bearer valid-token",
            "X-Device-Health": "bad"
        },
        "client": ("127.0.0.1", 12345)
    })
    with pytest.raises(HTTPException) as excinfo:
        await zero_trust_manager.verify_request(request)
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Device posture too risky"
