# backend_api/threat_intelligence_service/app.py

import os
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, HTTPException, Query, APIRouter
from pydantic import BaseModel
from datetime import datetime
from contextlib import asynccontextmanager # Import for lifespan
import uvicorn # Import uvicorn for standalone execution

from shared.logger_config import logger
from .models import UTMResult, IndicatorBase
from .enrichment import ThreatIntelligenceEnricher
from .cache import threat_intel_cache

logger = logger

# --- SAFE MODE ---
SAFE_MODE = False
SAFE_MODE_REASON = ""

router = APIRouter()

# Initialize the enricher
threat_enricher = ThreatIntelligenceEnricher()

class IndicatorLookup(BaseModel):
    value: str
    type: str

class BulkIndicatorLookup(BaseModel):
    indicators: List[IndicatorLookup]

async def threat_intel_startup():
    # Initialize the enricher
    # threat_enricher = ThreatIntelligenceEnricher() # Already initialized globally
    # The SAFE_MODE variables and logic will be handled in the main app's lifespan or configuration.
    logger.info("Threat Intelligence Service startup event triggered.")
    # Check for Redis connection
    if threat_intel_cache.client is None:
        # SAFE_MODE = True # These are now local to this function if not global
        # SAFE_MODE_REASON = "Redis client not initialized."
        logger.critical(f"!!! SAFE MODE ACTIVATED: Redis client not initialized. !!!")
        logger.critical("!!! Threat intelligence will not be cached. Performance will be degraded. !!!")
    else:
        try:
            await threat_intel_cache.ping()
            logger.info("Redis cache connection successful.")
        except Exception as e:
            # SAFE_MODE = True
            # SAFE_MODE_REASON = f"Redis connection failed: {e}"
            logger.critical(f"!!! SAFE MODE ACTIVATED: Redis connection failed: {e} !!!")
            logger.critical("!!! Threat intelligence will not be cached. Performance will be degraded. !!!")

async def threat_intel_shutdown():
    logger.info("Threat Intelligence Service shutting down.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await threat_intel_startup()
    yield
    await threat_intel_shutdown()

app = FastAPI(title="Threat Intelligence Service", lifespan=lifespan)
app.include_router(router, prefix="/api")


@router.get("/health")
async def health_check():
    if SAFE_MODE:
        return {
            "status": "degraded",
            "message": "Threat Intelligence Service is running in SAFE MODE.",
            "reason": SAFE_MODE_REASON
        }
    return {"status": "ok", "message": "Threat Intelligence Service is healthy"}

@router.post("/threat-intel/lookup", response_model=UTMResult)
async def lookup_indicator(indicator: IndicatorLookup):
    """
    Performs a real-time lookup and enrichment for a single threat indicator.
    """
    use_cache = not SAFE_MODE
    if SAFE_MODE:
        logger.warning(f"SAFE MODE: Bypassing cache for lookup of {indicator.value}")

    try:
        result = await threat_enricher.enrich_indicator(indicator.value, indicator.type, use_cache=use_cache)
        return result
    except Exception as e:
        logger.error(f"Error looking up indicator {indicator.value} ({indicator.type}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to lookup indicator: {e}")

@router.post("/threat-intel/bulk", response_model=List[UTMResult])
async def bulk_lookup_indicators(bulk_lookup: BulkIndicatorLookup):
    """
    Performs a bulk lookup and enrichment for multiple threat indicators concurrently.
    """
    tasks = []
    use_cache_in_bulk = not SAFE_MODE
    if SAFE_MODE:
        logger.warning("SAFE MODE: Bypassing cache for bulk lookup.")

    for indicator in bulk_lookup.indicators:
        tasks.append(threat_enricher.enrich_indicator(indicator.value, indicator.type, use_cache=use_cache_in_bulk))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    response_results = []
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            logger.error(f"Error in bulk lookup for {bulk_lookup.indicators[i].value}: {res}")
            response_results.append(UTMResult(
                indicator=bulk_lookup.indicators[i],
                raw_responses={"error": str(res)},
                is_malicious=False
            ))
        else:
            response_results.append(res)
            
    return response_results

@router.get("/threat-intel/history", response_model=List[UTMResult])
async def get_indicator_history(
    value: str = Query(..., description="The indicator value (IP, domain, hash, URL, Cloud Resource ID)."),
    type: str = Query(..., description="The type of the indicator (e.g., 'ip', 'domain').")
):
    """
    Retrieves historical threat intelligence data for a given indicator.
    (Conceptual: This would query a historical database or log of past enrichments.)
    For now, it returns the current lookup result as a single-item list.
    """
    logger.warning("Historical lookup is conceptual. Returning current lookup as history.")
    use_cache = not SAFE_MODE

    try:
        result = await threat_enricher.enrich_indicator(value, type, use_cache=use_cache)
        return [result]
    except Exception as e:
        logger.error(f"Error getting history for indicator {value} ({type}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {e}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8015, reload=True) # Assuming 8015 is the port for TI service
