from __future__ import annotations

import asyncio
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, FastAPI
from loguru import logger
from pydantic import BaseModel, Field

from backend_api.core.response import error_response, success_response
from backend_api.iam_service.policy import require_capability
from backend_api.shared.database import User
from backend_api.shared.service_factory import create_phantom_service
from .cache import threat_intel_cache
from .enrichment import ThreatIntelligenceEnricher


PUBLIC_INDICATOR_TYPES = Literal["ip", "domain", "hash", "url"]
MAX_BULK_LOOKUPS = 50

threat_enricher = ThreatIntelligenceEnricher()
router = APIRouter()


async def ti_startup(app: FastAPI) -> None:
    """Report cache availability without treating this optional performance layer as readiness."""
    if threat_intel_cache.client:
        try:
            await threat_intel_cache.ping()
            logger.info("Threat intelligence Redis cache connection verified.")
        except Exception:
            logger.exception("Threat intelligence Redis cache probe failed; cache remains unavailable.")
    else:
        logger.info("Threat intelligence Redis cache is not configured; enrichment will run without caching.")


app = create_phantom_service(
    name="Threat Intelligence Service",
    description="Capability-protected advisory indicator enrichment with bounded external-provider exposure.",
    version="1.0.0",
    custom_startup=ti_startup,
    required_dependencies=(),
)
class IndicatorLookup(BaseModel):
    value: Annotated[str, Field(min_length=1, max_length=2048)]
    type: PUBLIC_INDICATOR_TYPES


def _safe_enrichment_view(result: Any) -> dict[str, Any]:
    """Return advisory enrichment without relaying provider payloads, credentials, or exception detail."""
    payload = result.model_dump(mode="json")
    raw_responses = payload.pop("raw_responses", {})
    payload["provider_status"] = {
        provider: "unavailable" if _provider_response_is_unavailable(response) else "available"
        for provider, response in raw_responses.items()
    }
    return payload


def _provider_response_is_unavailable(response: Any) -> bool:
    return not response or (
        isinstance(response, dict)
        and ("error" in response or response.get("status") == "offline_fallback_activated" or "message" in response)
    )


async def _safe_bulk_lookup(indicator: IndicatorLookup) -> dict[str, Any]:
    try:
        result = await threat_enricher.enrich_indicator(indicator.value, indicator.type)
        return {
            "indicator": {"value": indicator.value, "type": indicator.type},
            "result": _safe_enrichment_view(result),
        }
    except Exception:
        logger.exception("Threat intelligence bulk enrichment failed.")
        return {
            "indicator": {"value": indicator.value, "type": indicator.type},
            "error": {
                "code": "ENRICHMENT_UNAVAILABLE",
                "message": "Indicator enrichment is temporarily unavailable.",
            },
        }


@router.post("/threat-intel/lookup")
async def lookup_indicator(
    indicator: IndicatorLookup,
    current_user: User = Depends(require_capability("alerts:read")),
):
    try:
        result = await threat_enricher.enrich_indicator(indicator.value, indicator.type)
    except Exception:
        logger.exception("Threat intelligence enrichment failed.")
        return error_response(
            code="ENRICHMENT_UNAVAILABLE",
            message="Indicator enrichment is temporarily unavailable.",
            status_code=503,
        )
    return success_response(data=_safe_enrichment_view(result))


@router.post("/threat-intel/bulk")
async def bulk_lookup_indicators(
    bulk_lookup: Annotated[list[IndicatorLookup], Field(min_length=1, max_length=MAX_BULK_LOOKUPS)],
    current_user: User = Depends(require_capability("alerts:read")),
):
    results = await asyncio.gather(*(_safe_bulk_lookup(indicator) for indicator in bulk_lookup))
    return success_response(data=results)


app.include_router(router, prefix="/api")
