from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend_api"
MIGRATION_HEAD = "d9e0f1a2b3c4"


def _config(database_path: Path) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{database_path}")
    return config


def test_autonomous_defense_migration_upgrades_clean_database_to_head(tmp_path):
    database_path = tmp_path / "autonomous-defense-migration.sqlite"
    config = _config(database_path)

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    try:
        inspector = inspect(engine)
        assert "autonomous_defense_policies" in inspector.get_table_names()
        assert "autonomous_defense_decisions" in inspector.get_table_names()
        assert "defensive_dataset_sources" in inspector.get_table_names()
        assert "defensive_dataset_versions" in inspector.get_table_names()
        assert "defensive_dataset_samples" in inspector.get_table_names()
        assert "defensive_evaluation_policies" in inspector.get_table_names()
        assert "defensive_model_evaluations" in inspector.get_table_names()
        assert "advisory_model_assessments" in inspector.get_table_names()
        assert "telemetry_agent_credentials" in inspector.get_table_names()
        assert "telemetry_signature_nonces" in inspector.get_table_names()
        policy_columns = {column["name"] for column in inspector.get_columns("autonomous_defense_policies")}
        decision_columns = {column["name"] for column in inspector.get_columns("autonomous_defense_decisions")}
        dataset_columns = {column["name"] for column in inspector.get_columns("defensive_dataset_versions")}
        evaluation_columns = {column["name"] for column in inspector.get_columns("defensive_model_evaluations")}
        assessment_columns = {column["name"] for column in inspector.get_columns("advisory_model_assessments")}
        telemetry_credential_columns = {column["name"] for column in inspector.get_columns("telemetry_agent_credentials")}
        telemetry_nonce_columns = {column["name"] for column in inspector.get_columns("telemetry_signature_nonces")}
        assert {"policy_id", "tenant_id", "decision_mode", "minimum_confidence"} <= policy_columns
        assert {
            "decision_id",
            "tenant_id",
            "evidence_ids",
            "containment_request_id",
            "requires_human_approval",
            "decision_hash",
        } <= decision_columns
        assert {"dataset_id", "source_id", "dataset_fingerprint", "intended_use", "sanitization_attested"} <= dataset_columns
        assert {
            "evaluation_id",
            "dataset_id",
            "model_id",
            "evaluation_fingerprint",
            "advisory_only",
            "requires_human_approval",
            "automatic_enforcement",
        } <= evaluation_columns
        assert {
            "assessment_id",
            "detection_id",
            "evaluation_id",
            "evidence_ids",
            "recommended_mode",
            "advisory_only",
            "requires_human_approval",
            "automatic_enforcement",
        } <= assessment_columns
        assert {"credential_id", "tenant_id", "agent_id", "key_id", "public_key_pem", "status", "revoked_at"} <= telemetry_credential_columns
        assert {"nonce_record_id", "tenant_id", "agent_id", "key_id", "nonce", "payload_sha256", "signed_at", "accepted_at"} <= telemetry_nonce_columns
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == MIGRATION_HEAD
    finally:
        engine.dispose()
