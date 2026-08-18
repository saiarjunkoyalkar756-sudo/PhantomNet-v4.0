import os

import pytest

from backend_api.shared import secret_manager
from backend_api.shared.settings import Settings


CRITICAL_KEYS = ("JWT_SECRET_KEY", "DB_PASSWORD", "NEO4J_PASSWORD")


def _clear_critical_environment(monkeypatch):
    for key in CRITICAL_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_development_secret_validation_generates_ephemeral_values_without_logging_them(monkeypatch):
    _clear_critical_environment(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "development")
    log_messages = []
    monkeypatch.setattr(secret_manager.logger, "warning", lambda message, **kwargs: log_messages.append((message, kwargs)))

    secret_manager.validate_secrets()
    generated_values = [os.environ[key] for key in CRITICAL_KEYS]

    assert all(len(value) == 64 for value in generated_values)
    assert all(value not in str(log_messages) for value in generated_values)
    assert all("before deployment" in message for message, _ in log_messages)


def test_production_secret_validation_rejects_missing_environment_values(monkeypatch):
    _clear_critical_environment(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "production")

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        secret_manager.validate_secrets()


def test_production_secret_validation_rejects_known_insecure_values_without_echoing_them(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "a_very_secret_key_that_should_be_changed")
    monkeypatch.setenv("DB_PASSWORD", "long-enough-password-123")
    monkeypatch.setenv("NEO4J_PASSWORD", "long-enough-password-123")

    with pytest.raises(ValueError) as rejected:
        secret_manager.validate_secrets()

    assert "a_very_secret_key" not in str(rejected.value)
    assert "JWT_SECRET_KEY" in str(rejected.value)


def test_settings_do_not_embed_secret_defaults_and_require_jwt_when_safe_mode_is_disabled(monkeypatch):
    _clear_critical_environment(monkeypatch)
    safe_settings = Settings(SAFE_MODE=True)
    assert safe_settings.JWT_SECRET_KEY is None
    assert safe_settings.DB_PASSWORD is None
    assert safe_settings.NEO4J_PASSWORD is None
    assert "@" in safe_settings.DATABASE_URL
    assert "changeme" not in safe_settings.DATABASE_URL

    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings(SAFE_MODE=False, JWT_SECRET_KEY=None)


def test_get_secret_refuses_missing_production_secret(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("RESPONSE_PROVIDER_TOKEN", raising=False)

    with pytest.raises(ValueError, match="RESPONSE_PROVIDER_TOKEN"):
        secret_manager.get_secret("RESPONSE_PROVIDER_TOKEN")
