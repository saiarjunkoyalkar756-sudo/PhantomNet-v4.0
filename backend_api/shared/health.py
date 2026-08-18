"""Structured health and readiness checks for PhantomNet microservices."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
import socket
from typing import Any, Awaitable, Callable, Dict
from urllib.parse import unquote, urlparse

from kafka import KafkaConsumer
from loguru import logger
import psycopg2
import redis

from backend_api.core_config import SAFE_MODE
from backend_api.shared.runtime_posture import assess_runtime_posture
from backend_api.shared.settings import settings


HealthCheck = Callable[[], Awaitable[Dict[str, Any]]]
DEFAULT_DEPENDENCIES = ("database", "kafka", "redis")


def _disabled_dependency(name: str) -> Dict[str, Any]:
    return {
        "status": "disabled",
        "required": False,
        "reason": "safe_mode",
        "message": f"{name} connectivity is intentionally not exercised while PHANTOMNET_SAFE_MODE is enabled.",
    }


def _unhealthy_dependency(code: str, exc: Exception) -> Dict[str, Any]:
    logger.error("Dependency readiness check failed", code=code, error_type=type(exc).__name__)
    return {"status": "unhealthy", "error_code": code, "error_type": type(exc).__name__}


async def check_db_health() -> Dict[str, Any]:
    """Verify PostgreSQL queryability without exposing connection details."""
    if SAFE_MODE:
        return _disabled_dependency("database")

    def _check() -> None:
        database_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)
        parsed = urlparse(database_url)
        connect_args: Dict[str, Any] = {
            "dbname": parsed.path.lstrip("/"),
            "user": unquote(parsed.username) if parsed.username else None,
            "password": unquote(parsed.password) if parsed.password else settings.DB_PASSWORD,
            "host": parsed.hostname,
            "port": parsed.port,
            "connect_timeout": 2,
        }
        connection = psycopg2.connect(**{key: value for key, value in connect_args.items() if value is not None})
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
        finally:
            connection.close()

    try:
        await asyncio.get_running_loop().run_in_executor(None, _check)
        return {"status": "healthy"}
    except Exception as exc:
        return _unhealthy_dependency("DATABASE_UNAVAILABLE", exc)


async def check_kafka_health() -> Dict[str, Any]:
    """Verify Kafka or Redpanda metadata access without creating a consuming workload."""
    if SAFE_MODE:
        return _disabled_dependency("kafka")

    def _check() -> None:
        consumer = KafkaConsumer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=2_000,
            api_version_auto_timeout_ms=2_000,
        )
        try:
            consumer.topics()
        finally:
            consumer.close()

    try:
        await asyncio.get_running_loop().run_in_executor(None, _check)
        return {"status": "healthy"}
    except Exception as exc:
        return _unhealthy_dependency("KAFKA_UNAVAILABLE", exc)


async def check_redis_health() -> Dict[str, Any]:
    """Verify Redis reachability without revealing endpoint or authentication details."""
    if SAFE_MODE:
        return _disabled_dependency("redis")

    def _check() -> None:
        client = (
            redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2)
            if settings.REDIS_URL
            else redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, socket_timeout=2)
        )
        try:
            client.ping()
        finally:
            client.close()

    try:
        await asyncio.get_running_loop().run_in_executor(None, _check)
        return {"status": "healthy"}
    except Exception as exc:
        return _unhealthy_dependency("REDIS_UNAVAILABLE", exc)


async def check_neo4j_health() -> Dict[str, Any]:
    """Verify Neo4j Bolt reachability when a service declares graph dependency."""
    if SAFE_MODE:
        return _disabled_dependency("neo4j")
    def _check() -> None:
        connection = socket.create_connection((settings.NEO4J_HOST, settings.NEO4J_PORT), timeout=2)
        connection.close()

    try:
        await asyncio.wait_for(asyncio.get_running_loop().run_in_executor(None, _check), timeout=3)
        return {"status": "healthy", "verification": "bolt_port_reachable"}
    except Exception as exc:
        return _unhealthy_dependency("NEO4J_UNAVAILABLE", exc)


HEALTH_CHECKS: Dict[str, HealthCheck] = {
    "database": check_db_health,
    "kafka": check_kafka_health,
    "redis": check_redis_health,
    "neo4j": check_neo4j_health,
}


async def run_standard_health_check(required_dependencies: Iterable[str] | None = None) -> Dict[str, Any]:
    """Return readiness evidence for explicitly declared upstream dependencies.

    A service can be healthy as a process while not ready to enforce protections. In safe
    mode, dependency checks are reported as disabled and readiness is intentionally false.
    """
    dependency_names = tuple(required_dependencies or DEFAULT_DEPENDENCIES)
    unknown_dependencies = sorted(set(dependency_names).difference(HEALTH_CHECKS))
    if unknown_dependencies:
        raise ValueError(f"Unknown health dependencies: {', '.join(unknown_dependencies)}")

    checks = await asyncio.gather(*(HEALTH_CHECKS[name]() for name in dependency_names))
    components = dict(zip(dependency_names, checks, strict=True))
    unhealthy = [name for name, result in components.items() if result["status"] == "unhealthy"]
    security_posture = assess_runtime_posture(safe_mode=SAFE_MODE)

    if SAFE_MODE:
        return {
            "status": "healthy",
            "readiness": "safe_mode",
            "mode": "safe",
            "components": components,
            "required_dependencies": list(dependency_names),
            "security_posture": security_posture,
        }
    ready = not unhealthy and security_posture["status"] == "ready"
    return {
        "status": "healthy" if ready else "degraded",
        "readiness": "ready" if ready else "not_ready",
        "mode": "active",
        "components": components,
        "required_dependencies": list(dependency_names),
        "security_posture": security_posture,
    }
