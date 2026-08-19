from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.responses import JSONResponse

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
async def test_blockchain_data_returns_current_orm_blocks_in_success_envelope():
    block = SimpleNamespace(to_dict=lambda: {"index": 1, "block_hash": "genesis"})
    db = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: [block])
            )
        )
    )
    user = SimpleNamespace(username="auditor")

    response = await get_blockchain_data(current_user=user, db=db)

    assert response["success"] is True
    assert response["data"] == {"chain": [{"index": 1, "block_hash": "genesis"}]}


@pytest.mark.asyncio
async def test_blockchain_integrity_endpoint_returns_verified_status():
    blockchain = SimpleNamespace(is_chain_valid=AsyncMock(return_value=True))

    response = await verify_blockchain_integrity(blockchain=blockchain)

    assert response["success"] is True
    assert response["data"]["message"] == "Blockchain integrity verified: All blocks are valid."
