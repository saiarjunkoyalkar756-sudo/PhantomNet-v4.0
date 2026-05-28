# backend_api/shared/exceptions.py

class PhantomNetBaseError(Exception):
    """Base exception for all PhantomNet errors."""
    def __init__(self, message: str = "A platform error occurred.", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(PhantomNetBaseError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed."):
        super().__init__(message, status_code=401)


class AuthorizationError(PhantomNetBaseError):
    """Raised when authorization (permission check) fails."""
    def __init__(self, message: str = "Permission denied."):
        super().__init__(message, status_code=403)


class ServiceUnavailableError(PhantomNetBaseError):
    """Raised when a dependent downstream service is unreachable."""
    def __init__(self, message: str = "Service unavailable."):
        super().__init__(message, status_code=503)


class KafkaConnectionError(ServiceUnavailableError):
    """Raised when a connection to Redpanda/Kafka fails."""
    def __init__(self, message: str = "Kafka broker is unreachable."):
        super().__init__(message)


class DatabaseConnectionError(ServiceUnavailableError):
    """Raised when a connection to the PostgreSQL database fails."""
    def __init__(self, message: str = "Database is unreachable."):
        super().__init__(message)


class ValidationError(PhantomNetBaseError):
    """Raised when validation (input or schema) fails."""
    def __init__(self, message: str = "Validation failed."):
        super().__init__(message, status_code=400)


class DetectionError(PhantomNetBaseError):
    """Raised when a threat detection algorithm or rule fails to execute."""
    def __init__(self, message: str = "Detection engine error occurred."):
        super().__init__(message, status_code=500)
