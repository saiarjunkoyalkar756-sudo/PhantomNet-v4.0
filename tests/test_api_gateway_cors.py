from __future__ import annotations

import ast
from pathlib import Path

from starlette.middleware.cors import CORSMiddleware

from backend_api.shared.service_factory import create_phantom_service


ROOT = Path(__file__).resolve().parents[1]
GATEWAY_SOURCE = ROOT / "backend_api/api_gateway/app.py"
SELF_HOSTED_GATEWAY_SOURCE = ROOT / "backend_api/gateway_service/main.py"


def _cors_options(app) -> dict:
    middleware = next(item for item in app.user_middleware if item.cls is CORSMiddleware)
    return middleware.kwargs


def _factory_keywords(path: Path) -> dict[str, ast.expr]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    factory_calls = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "create_phantom_service"
    ]
    assert len(factory_calls) == 1
    return {keyword.arg: keyword.value for keyword in factory_calls[0].keywords if keyword.arg}


def test_production_service_factory_cors_policy_never_uses_a_wildcard(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    app = create_phantom_service("Gateway CORS Test", "Validates origin restrictions.")
    options = _cors_options(app)

    assert options["allow_origins"] == ["https://phantomnet.io", "https://api.phantomnet.io"]
    assert "*" not in options["allow_origins"]
    assert options["allow_credentials"] is True


def test_both_gateway_entrypoints_defer_to_shared_environment_scoped_cors_policy():
    for path in (GATEWAY_SOURCE, SELF_HOSTED_GATEWAY_SOURCE):
        assert "cors_origins" not in _factory_keywords(path)
        assert '"*"' not in path.read_text(encoding="utf-8")
