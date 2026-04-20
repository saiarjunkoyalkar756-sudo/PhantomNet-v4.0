from backend_api.shared.service_factory import create_phantom_service
from .enrichment import ThreatIntelligenceEnricher
from .cache import threat_intel_cache
from loguru import logger
import asyncio
from typing import List
from backend_api.core.response import success_response, error_response
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

threat_enricher = ThreatIntelligenceEnricher()
router = APIRouter()

async def ti_startup(app: FastAPI):
    # Startup check for cache
    if threat_intel_cache.client:
        try:
            await threat_intel_cache.ping()
            logger.info("Threat Intel: Redis cache connection successful.")
        except Exception:
            logger.warning("Threat Intel: Redis connection failed, running in degraded mode.")

app = create_phantom_service(
    name="Threat Intelligence Service",
    description="Real-time indicator enrichment and threat scoring.",
    version="1.0.0",
    custom_startup=ti_startup
)

app.include_router(router, prefix="/api")

class IndicatorLookup(BaseModel):
    value: str
    type: str

@router.post("/threat-intel/lookup")
async def lookup_indicator(indicator: IndicatorLookup):
    try:
        result = await threat_enricher.enrich_indicator(indicator.value, indicator.type)
        return success_response(data=result)
    except Exception as e:
        return error_response(code="ENRICHMENT_FAILED", message=str(e), status_code=500)

@router.post("/threat-intel/bulk")
async def bulk_lookup_indicators(bulk_lookup: List[IndicatorLookup]):
    tasks = [threat_enricher.enrich_indicator(i.value, i.type) for i in bulk_lookup]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return success_response(data=results)
