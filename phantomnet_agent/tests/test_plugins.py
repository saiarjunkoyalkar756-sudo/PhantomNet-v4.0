import pytest
import asyncio
from unittest.mock import MagicMock, patch
from pathlib import Path
import json

from phantomnet_agent.plugins.loader import PluginLoader, PluginManifest
from phantomnet_agent.plugins.sandbox import PluginSandbox
from phantomnet_agent.bus.base import Transport

@pytest.fixture
def temp_plugin_dir(tmp_path):
    """Creates a temporary directory structure for plugin tests."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    return plugin_dir

@pytest.fixture
def mock_transport():
    """Mock transport for plugin functions that might use it."""
    mock_transport = MagicMock(spec=Transport)
    mock_transport.send_event = AsyncMock()
    mock_transport.receive_commands = MagicMock(return_value=(a for a in ())) # Async empty generator
    return mock_transport


# --- PluginLoader Tests ---
@pytest.mark.asyncio
async def test_plugin_loader_load_valid_plugin(temp_plugin_dir):
    # Create a valid plugin
    valid_plugin_path = temp_plugin_dir / "my_scanner"
    valid_plugin_path.mkdir()
    (valid_plugin_path / "plugin.json").write_text(json.dumps({
        "name": "my_scanner",
        "version": "1.0.0",
        "entry": "scanner_module:scan_host",
        "description": "Scans a host.",
        "permissions": ["network:scan"]
    }))
    (valid_plugin_path / "scanner_module.py").write_text("""
import asyncio
async def scan_host(target: str, transport):
    await asyncio.sleep(0.01)
    return {"result": f"Scanned {target}"}
""")

    loader = PluginLoader(plugin_dirs=[temp_plugin_dir], allowed_permissions=["network:scan"])
    loaded_plugins = loader.load_plugins()

    assert "my_scanner" in loaded_plugins
    plugin = loaded_plugins["my_scanner"]
    assert plugin.manifest.name == "my_scanner"
    assert plugin.manifest.version == "1.0.0"
    assert plugin.manifest.permissions == ["network:scan"]
    
    # Test entrypoint can be called
    entrypoint = plugin.get_entrypoint()
    result = await entrypoint(target="localhost", transport=mock_transport)
    assert result == {"result": "Scanned localhost"}


@pytest.mark.asyncio
async def test_plugin_loader_unallowed_permissions(temp_plugin_dir):
    # Create a plugin with unallowed permissions
    bad_plugin_path = temp_plugin_dir / "bad_plugin"
    bad_plugin_path.mkdir()
    (bad_plugin_path / "plugin.json").write_text(json.dumps({
        "name": "bad_plugin",
        "version": "1.0.0",
        "entry": "bad_module:do_something",
        "permissions": ["system:root_access"]
    }))
    (bad_plugin_path / "bad_module.py").write_text("def do_something(): pass")

    loader = PluginLoader(plugin_dirs=[temp_plugin_dir], allowed_permissions=["network:scan"])
    loaded_plugins = loader.load_plugins()

    assert "bad_plugin" not in loaded_plugins


@pytest.mark.asyncio
async def test_plugin_loader_malformed_manifest(temp_plugin_dir):
    # Create a plugin with a malformed manifest
    malformed_plugin_path = temp_plugin_dir / "malformed_plugin"
    malformed_plugin_path.mkdir()
    (malformed_plugin_path / "plugin.json").write_text("this is not json")
    (malformed_plugin_path / "malformed_module.py").write_text("def func(): pass")

    loader = PluginLoader(plugin_dirs=[temp_plugin_dir], allowed_permissions=[])
    loaded_plugins = loader.load_plugins()

    assert "malformed_plugin" not in loaded_plugins


# --- PluginSandbox Tests ---
@pytest.mark.asyncio
async def test_plugin_sandbox_fast_function():
    sandbox = PluginSandbox(timeout_seconds=1)
    async def fast_func():
        await asyncio.sleep(0.01)
        return "fast"
    result = await sandbox.run_plugin_function(fast_func)
    assert result == {"status": "success", "result": "fast"}

@pytest.mark.asyncio
async def test_plugin_sandbox_timeout_function():
    sandbox = PluginSandbox(timeout_seconds=0.1) # Very short timeout
    async def slow_func():
        await asyncio.sleep(0.5) # Longer than timeout
        return "slow"
    result = await sandbox.run_plugin_function(slow_func)
    assert result["status"] == "failed"
    assert "timed out" in result["reason"]

@pytest.mark.asyncio
async def test_plugin_sandbox_function_with_exception():
    sandbox = PluginSandbox(timeout_seconds=1)
    async def error_func():
        raise ValueError("test error")
    result = await sandbox.run_plugin_function(error_func)
    assert result["status"] == "failed"
    assert "test error" in result["reason"]

