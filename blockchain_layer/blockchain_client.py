import json
import httpx
import os

# The collector service is running on port 8001
COLLECTOR_API_URL = os.getenv(
    "COLLECTOR_API_URL", "http://localhost:8001"
)  # Use env var for flexibility


async def _submit_data_to_collector(endpoint: str, payload: dict, data_type: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{COLLECTOR_API_URL}/{endpoint}",
                json={**payload, "data_type": data_type},  # Add data_type to payload
            )
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            print(
                f"[Blockchain Client] Data submitted to collector ({data_type}): {response.json()}"
            )
    except httpx.RequestError as exc:
        print(
            f"[Blockchain Client] An error occurred while requesting {exc.request.url!r}: {exc}"
        )
    except httpx.HTTPStatusError as exc:
        print(
            f"[Blockchain Client] Error response {exc.response.status_code} while requesting {exc.request.url!r}: {exc.response.text}"
        )


async def submit_log_to_ledger(ip, port, data):
    """Submits raw log data to the collector service."""
    await _submit_data_to_collector(
        endpoint="logs/ingest",
        payload={"ip": ip, "port": port, "data": data},
        data_type="attack_log",
    )


async def submit_alert_to_ledger(
    alert_id: str, alert_name: str, severity: str, event_data: dict
):
    """Submits alert data to the collector service."""
    await _submit_data_to_collector(
        endpoint="alerts/ingest",  # Assuming a new endpoint for alerts
        payload={
            "alert_id": alert_id,
            "alert_name": alert_name,
            "severity": severity,
            "event_data": json.dumps(event_data),  # Store event data as JSON string
        },
        data_type="alert",
    )


async def submit_normalized_event_to_ledger(
    event_id: str, timestamp: float, source: str, event_type: str, details: dict
):
    """Submits normalized event data to the collector service."""
    await _submit_data_to_collector(
        endpoint="normalized_events/ingest",  # Assuming a new endpoint for normalized events
        payload={
            "event_id": event_id,
            "timestamp": timestamp,
            "source": source,
            "event_type": event_type,
            "details": json.dumps(details),  # Store details as JSON string
        },
        data_type="normalized_event",
    )


async def submit_forensic_record_to_ledger(
    record_id: str, tool_name: str, results: dict
):
    """Submits forensic record data to the collector service."""
    await _submit_data_to_collector(
        endpoint="forensic_records/ingest",  # Assuming a new endpoint for forensic records
        payload={
            "record_id": record_id,
            "tool_name": tool_name,
            "results": json.dumps(results),  # Store results as JSON string
        },
        data_type="forensic_record",
    )
