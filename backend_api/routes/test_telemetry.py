from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend_api.routes.telemetry import CustomLogEntry, ingest_custom_log


@pytest.mark.asyncio
async def test_ingest_custom_log_forwards_structured_log_to_service():
    telemetry_service = AsyncMock()
    log = CustomLogEntry(
        source="my-custom-app",
        log_entry={"message": "This is a custom log message", "level": "info"},
    )

    response = await ingest_custom_log(log, current_user=object(), telemetry_service=telemetry_service)

    assert response == {"message": "Log entry accepted for ingestion."}
    telemetry_service.ingest_raw_log.assert_awaited_once_with(log.log_entry, log.source)


@pytest.mark.asyncio
async def test_ingest_custom_log_fails_closed_when_service_is_unavailable():
    log = CustomLogEntry(source="my-custom-app", log_entry="test log")

    with pytest.raises(HTTPException) as exc_info:
        await ingest_custom_log(log, current_user=object(), telemetry_service=None)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Telemetry Ingest Service not available."
