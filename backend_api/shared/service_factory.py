from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os
import time
import json
import uuid
from typing import Optional, Callable, Dict, Any, List
from loguru import logger
from backend_api.shared.logger_config import setup_logging, async_log_sink
from backend_api.core.response import success_response, error_response

def create_phantom_service(
    name: str,
    description: str,
    version: str = "1.0.0",
    custom_startup: Optional[Callable] = None,
    custom_shutdown: Optional[Callable] = None,
    use_standard_envelope: bool = True,
    cors_origins: Optional[List[str]] = None,
) -> FastAPI:
    """
    Standardized factory to create a 'Strong' PhantomNet microservice.
    Enforces lifespan management, structured logging, and unified response envelopes.
    """
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 1. Standardized Startup
        setup_logging(name=name)
        log_task = asyncio.create_task(async_log_sink())
        logger.info(f"Service '{name}' (v{version}) starting up...")
        
        # 2. Run custom startup logic if provided
        if custom_startup:
            if asyncio.iscoroutinefunction(custom_startup):
                await custom_startup(app)
            else:
                custom_startup(app)
        
        yield
        
        # 3. Standardized Shutdown
        logger.info(f"Service '{name}' shutting down...")
        
        if custom_shutdown:
            if asyncio.iscoroutinefunction(custom_shutdown):
                await custom_shutdown(app)
            else:
                custom_shutdown(app)
            
        log_task.cancel()
        try:
            await asyncio.gather(log_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass
        
        logger.info(f"Service '{name}' shutdown complete.")

    app = FastAPI(
        title=name,
        description=description,
        version=version,
        lifespan=lifespan
    )

    # Standard Middleware: Security Headers
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-Service-Name"] = name
        return response

    # Standard Middleware: Request ID and Process Time
    @app.middleware("http")
    async def process_metadata_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response

    # Standard Middleware: Response Enveloping
    if use_standard_envelope:
        @app.middleware("http")
        async def response_envelope_middleware(request: Request, call_next):
            # Skip for docs and websockets
            if any(request.url.path.startswith(p) for p in ["/docs", "/redoc", "/openapi.json", "/ws"]):
                return await call_next(request)
                
            response = await call_next(request)
            
            # Already handled error or non-JSON
            if response.status_code >= 400 or "application/json" not in response.headers.get("Content-Type", ""):
                return response
                
            try:
                # We need to capture the body. Note: This can be expensive for large responses.
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                data = json.loads(body)
                
                # If already wrapped, just pass through
                if isinstance(data, dict) and "success" in data:
                    return JSONResponse(status_code=response.status_code, content=data)
                
                wrapped = success_response(data=data, request_id=getattr(request.state, "request_id", None))
                return JSONResponse(status_code=response.status_code, content=wrapped)
            except Exception:
                # Fallback to original response on failure
                return response

    # Default health check
    @app.get("/health", tags=["Infrastructure"])
    async def health_check():
        return success_response(data={
            "status": "online",
            "service": name,
            "version": version
        })

    # Global Exception Handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return error_response(
            code=f"HTTP_{exc.status_code}",
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=getattr(request.state, "request_id", None)
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception in {name}: {exc}", exc_info=True)
        return error_response(
            code="INTERNAL_SERVER_ERROR",
            message="Critical service failure. Incident logged.",
            status_code=500,
            request_id=getattr(request.state, "request_id", None)
        )

    # CORS configuration
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app
