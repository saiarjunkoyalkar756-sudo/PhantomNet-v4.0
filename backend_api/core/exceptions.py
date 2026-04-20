# backend_api/core/exceptions.py
from typing import Optional, Any

class PhantomNetException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Any] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AuthError(PhantomNetException):
    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__("AUTH_ERROR", message, 401, details)

class NotFoundError(PhantomNetException):
    def __init__(self, resource: str, resource_id: Any):
        super().__init__("NOT_FOUND", f"{resource} with id {resource_id} not found", 404)

class ValidationError(PhantomNetException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__("VALIDATION_ERROR", message, 422, details)

class ServiceUnavailableError(PhantomNetException):
    def __init__(self, service_name: str):
        super().__init__("SERVICE_UNAVAILABLE", f"Service {service_name} is currently unavailable", 503)
