from backend_api.shared.service_factory import create_phantom_service
import time
import uuid
import os
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend_api.core.response import error_response, success_response
from backend_api.core.exceptions import PhantomNetException
from loguru import logger

# Import Routers
from backend_api.gateway_service.admin import router as admin_router
from backend_api.gateway_service.agent_api import router as agent_router
from backend_api.gateway_service.orchestrator_api import router as orchestrator_router
from backend_api.iam_service.api import router as auth_router

# Setup Rate Limiter
limiter = Limiter(key_func=get_remote_address, storage_uri=os.getenv("REDIS_URL", "memory://"))

app = create_phantom_service(
    name="PhantomNet API Gateway",
    description="Secure entry point for the PhantomNet Microservice Grid.",
    version="3.0.0",
    cors_origins=["*"] # Tighten in production
)

app.state.limiter = limiter

# Exception Handlers
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return error_response(
        code="RATE_LIMIT_EXCEEDED",
        message="Too many requests. Please slow down.",
        status_code=429,
        request_id=getattr(request.state, "request_id", None)
    )

@app.exception_handler(PhantomNetException)
async def phantomnet_exception_handler(request: Request, exc: PhantomNetException):
    return error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code,
        request_id=getattr(request.state, "request_id", None)
    )

# Include Routers
app.include_router(auth_router)
app.include_router(admin_router, prefix="/admin")
app.include_router(agent_router) # Prefix /agents is already inside agent_api.py router or paths
app.include_router(orchestrator_router) # Prefix /orchestrator is already inside orchestrator_api.py

@app.get("/health_status")
@limiter.limit("5/minute")
async def health_status(request: Request):
    """Specific health check for gateway with rate limiting."""
    return success_response(data={"status": "healthy", "version": "3.0.0", "timestamp": time.time()})
