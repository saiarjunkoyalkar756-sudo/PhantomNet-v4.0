from __future__ import annotations

import ast
from pathlib import Path

from backend_api.shared.service_factory import create_phantom_service


ROOT = Path(__file__).resolve().parents[1]
CORE_INGESTION_SERVICES = {
    "backend_api/telemetry_ingestor/main.py": ("kafka",),
    "backend_api/event_normalizer/main.py": ("kafka",),
    "backend_api/alert_storage/main.py": ("database", "kafka"),
    "backend_api/command_dispatcher/main.py": ("kafka",),
    "backend_api/ai_behavioral_engine/main.py": ("kafka",),
}


def _declared_factory_dependencies(path: Path) -> tuple[str, ...]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "create_phantom_service"
    ]
    assert len(calls) == 1, f"Expected exactly one standardized service factory call in {path}."
    keywords = {keyword.arg: keyword.value for keyword in calls[0].keywords if keyword.arg}
    assert "required_dependencies" in keywords, f"{path} must declare explicit readiness dependencies."
    dependencies = ast.literal_eval(keywords["required_dependencies"])
    assert isinstance(dependencies, tuple)
    assert dependencies
    return dependencies


def test_core_ingestion_services_declare_only_their_actual_readiness_dependencies():
    for relative_path, expected_dependencies in CORE_INGESTION_SERVICES.items():
        assert _declared_factory_dependencies(ROOT / relative_path) == expected_dependencies


def test_standard_factory_retains_core_ingestion_dependency_contract_without_secret_material():
    app = create_phantom_service(
        "Core Ingestion Contract Test",
        "Validates explicit readiness dependencies.",
        required_dependencies=("database", "kafka"),
    )

    assert app.state.required_dependencies == ("database", "kafka")
    assert all("url" not in value and "password" not in value and "secret" not in value for value in app.state.required_dependencies)
