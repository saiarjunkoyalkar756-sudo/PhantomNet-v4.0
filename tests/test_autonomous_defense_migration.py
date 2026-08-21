from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend_api"
MIGRATION_HEAD = "a6b7c8d9e0f1"


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
        policy_columns = {column["name"] for column in inspector.get_columns("autonomous_defense_policies")}
        decision_columns = {column["name"] for column in inspector.get_columns("autonomous_defense_decisions")}
        assert {"policy_id", "tenant_id", "decision_mode", "minimum_confidence"} <= policy_columns
        assert {
            "decision_id",
            "tenant_id",
            "evidence_ids",
            "containment_request_id",
            "requires_human_approval",
            "decision_hash",
        } <= decision_columns
        with engine.connect() as connection:
            revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == MIGRATION_HEAD
    finally:
        engine.dispose()
