# backend_api/shared/resilience.py
import time
import logging
from enum import Enum
from typing import Callable, Any, Coroutine

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"  # Requests are allowed
    OPEN = "OPEN"      # Requests are blocked
    HALF_OPEN = "HALF_OPEN" # A limited number of requests are allowed to test for recovery

class CircuitBreaker:
    """
    A Circuit Breaker implementation to prevent repeated calls to a failing service.
    """
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30, # seconds
        half_open_attempts: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_attempts = half_open_attempts

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0
        self._half_open_success_count = 0

    @property
    def state(self) -> CircuitBreakerState:
        """
        Check the current state of the circuit breaker. If the recovery timeout has passed,
        move from OPEN to HALF_OPEN state.
        """
        if self._state == CircuitBreakerState.OPEN:
            if time.monotonic() - self._last_failure_time > self.recovery_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
                self._half_open_success_count = 0 # Reset for the new test window
                logger.warning("Circuit breaker moving to HALF_OPEN state.")
        return self._state

    def record_failure(self):
        """
        Records a failure. If the failure count exceeds the threshold,
        the circuit breaker is opened.
        """
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitBreakerState.OPEN
            self._last_failure_time = time.monotonic()
            logger.error(f"Circuit breaker OPENED due to {self._failure_count} failures.")

    def record_success(self):
        """
        Records a success. Resets the failure count in CLOSED state.
        In HALF_OPEN state, it checks if the service has recovered.
        """
        if self._state == CircuitBreakerState.HALF_OPEN:
            self._half_open_success_count += 1
            if self._half_open_success_count >= self.half_open_attempts:
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
                logger.info("Circuit breaker CLOSED after successful recovery.")
        else:
            self._failure_count = 0

    async def call(self, func: Callable[..., Coroutine], *args, **kwargs) -> Any:
        """
        Wraps an async function call with the circuit breaker logic.
        """
        if self.state == CircuitBreakerState.OPEN:
            raise ConnectionError("Circuit is open. Downstream service is likely unavailable.")
        
        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise e
