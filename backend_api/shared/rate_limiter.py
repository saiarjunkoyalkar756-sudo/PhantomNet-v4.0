# backend_api/shared/rate_limiter.py
"""
High-performance Redis-based Rate Limiter and Dynamic IP Blocker.
Provides standardized security controls for authentication and session endpoints.
"""

from fastapi import Request, HTTPException, status
from backend_api.shared.redis_client import redis_client
from loguru import logger

async def limit_auth_endpoint(request: Request, limit: int, window: int, endpoint_name: str):
    """
    Enforces Redis-based rate limiting on an endpoint.
    Blocks any access from IPs that have been blocked due to repeated failures.
    """
    ip = request.client.host if request.client else "unknown"
    
    # 1. Check if IP is explicitly blocked
    block_key = f"blocked_ips:{ip}"
    is_blocked = redis_client.get(block_key)
    if is_blocked:
        logger.warning(f"BLOCKED ACCESS: IP {ip} blocked from accessing {endpoint_name} due to security constraints.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access temporarily suspended due to repeated failed login attempts. Please try again in 5 minutes."
        )
        
    # 2. Increment request count and check rate limits
    rate_key = f"rate_limit:{endpoint_name}:{ip}"
    try:
        pipe = redis_client.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, window)
        request_count, _ = pipe.execute()
        
        if request_count > limit:
            logger.warning(f"RATE LIMIT EXCEEDED: IP {ip} throttled on {endpoint_name} ({request_count}/{limit} requests).")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again later."
            )
    except HTTPException:
        raise
    except Exception as err:
        # Fail-open design to prevent Redis failure from taking down authentication
        logger.error(f"Redis rate limiting pipeline failed: {err}. Failing open to preserve service uptime.")
        return

def log_failed_auth_attempt(ip: str):
    """
    Logs a failed authentication attempt.
    Tracks failures over a rolling 5-minute window; after 10 failures, blocks the IP for 5 minutes.
    """
    attempts_key = f"failed_attempts:{ip}"
    block_key = f"blocked_ips:{ip}"
    
    try:
        pipe = redis_client.pipeline()
        pipe.incr(attempts_key)
        pipe.expire(attempts_key, 300) # 5 minutes window
        failed_count, _ = pipe.execute()
        
        if failed_count >= 10:
            redis_client.setex(block_key, 300, "1") # Block IP for 300s (5m)
            redis_client.delete(attempts_key) # Reset attempts tracker
            logger.warning(f"SECURITY INCIDENT: IP {ip} has been blocked for 5 minutes after {failed_count} sequential failed authentication requests.")
    except Exception as err:
        logger.error(f"Failed authentication tracking failed: {err}.")
