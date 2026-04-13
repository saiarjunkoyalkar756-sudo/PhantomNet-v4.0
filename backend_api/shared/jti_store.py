import abc
from datetime import timedelta

class JtiStore(abc.ABC):
    @abc.abstractmethod
    def is_jti_used(self, jti: str) -> bool:
        """Check if a JTI has been used."""
        raise NotImplementedError

    @abc.abstractmethod
    def mark_jti_as_used(self, jti: str, expires_in: timedelta):
        """Mark a JTI as used, with an expiration."""
        raise NotImplementedError

class InMemoryJtiStore(JtiStore):
    """
    A simple in-memory JTI store for testing and development.
    This is not suitable for production as it's not persistent
    and won't work across multiple service instances.
    """
    def __init__(self):
        self._used_jtis = set()

    def is_jti_used(self, jti: str) -> bool:
        return jti in self._used_jtis

    def mark_jti_as_used(self, jti: str, expires_in: timedelta):
        # In-memory set doesn't support expiration, so we just add it.
        # A real implementation (e.g., Redis) would use the expires_in value.
        self._used_jtis.add(jti)

# Default store for convenience
default_jti_store = InMemoryJtiStore()
