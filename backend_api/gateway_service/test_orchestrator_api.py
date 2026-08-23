from fastapi.responses import JSONResponse

import pytest

from backend_api.gateway_service.orchestrator_api import (
    ThreatData,
    analyze_threat_endpoint,
    get_blockchain_data,
    verify_blockchain_integrity,
)


@pytest.mark.asyncio
async def test_threat_analysis_endpoint_is_explicitly_disabled():
    response = await analyze_threat_endpoint(ThreatData(threat_string="suspicious_activity"))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 501
    assert b"Orchestrator threat analysis is currently disabled." in response.body


@pytest.mark.asyncio
async def test_legacy_blockchain_data_route_is_explicitly_retired():
    response = await get_blockchain_data()

    assert isinstance(response, JSONResponse)
    assert response.status_code == 410
    assert b"LEGACY_GATEWAY_BLOCKCHAIN_API_RETIRED" in response.body


@pytest.mark.asyncio
async def test_legacy_blockchain_verification_route_is_explicitly_retired():
    response = await verify_blockchain_integrity()

    assert isinstance(response, JSONResponse)
    assert response.status_code == 410
    assert b"LEGACY_GATEWAY_BLOCKCHAIN_API_RETIRED" in response.body
