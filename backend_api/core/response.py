# backend_api/core/response.py
from datetime import datetime
from typing import Any, Optional
from fastapi.responses import JSONResponse

def success_response(data: Any, request_id: Optional[str] = None):
    return {
        "success": True,
        "data": data,
        "error": None,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat()
    }

def error_response(code: str, message: str, details: Optional[dict] = None, status_code: int = 400, request_id: Optional[str] = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            },
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
