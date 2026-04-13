import importlib.util
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from packaging.version import Version, InvalidVersion # For robust version comparison

from pydantic import ValidationError

from schemas.plugins import PluginManifest # Import PluginManifest from schemas
from core.state import get_agent_state # For getting agent_state.version
from utils.logger import get_logger # Use the structured logger

# Remove the redundant PluginManifest class definition from here

class Plugin:
    """Represents a loaded plugin module."""
    def __init__(self, manifest: PluginManifest, module):
        self.manifest = manifest
        self.module = module

    def get_entrypoint(self):
        """Returns the callable entrypoint function of the plugin."""
        module_name, func_name = self.manifest.entry.split(':')
        # Handle ClassName instantiation if entry is "module_name:ClassName"
        if hasattr(self.module, func_name) and isinstance(getattr(self.module, func_name), type):
            return getattr(self.module, func_name)() # Instantiate the class
        return getattr(self.module, func_name) # Assume it's a function

class PluginLoader:
    """
    Discovers, loads, and validates plugins from specified paths.
    """
    def __init__(self, plugin_dirs: List[Path], allowed_permissions: List[str]):
        self.logger = get_logger("phantomnet_agent.plugins.loader")
        self.plugin_dirs = plugin_dirs
        self.allowed_permissions = allowed_permissions
        self.agent_version = Version(get_agent_state().version) # Agent's current version for compatibility
        self.loaded_plugins: Dict[str, Plugin] = {}
        self.logger.info(f"PluginLoader initialized for agent version: {self.agent_version}")

    def load_plugins(self) -> Dict[str, Plugin]:
        """
        Scans plugin directories, loads valid plugins, and returns them.
        """
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.is_dir():
                self.logger.warning(f"Plugin directory not found: {plugin_dir}", extra={"plugin_dir": str(plugin_dir)})
                continue
            
            for plugin_path in plugin_dir.iterdir():
                if plugin_path.is_dir():
                    manifest_path = plugin_path / "plugin.json"
                    if manifest_path.is_file():
                        try:
                            manifest = self._load_manifest(manifest_path)
                            if not self._check_agent_version_compatibility(manifest):
                                self.logger.warning(f"Plugin '{manifest.name}' v{manifest.version} (Agent API v{manifest.phantomnet_agent_version}) is not compatible with agent version v{self.agent_version} and was not loaded.", extra={"plugin_name": manifest.name, "plugin_version": manifest.version, "plugin_agent_version": manifest.phantomnet_agent_version, "agent_version": self.agent_version})
                                continue

                            if self._validate_permissions(manifest):
                                plugin = self._load_plugin_module(plugin_path, manifest)
                                if plugin:
                                    self.loaded_plugins[manifest.name] = plugin
                                    self.logger.info(f"Loaded plugin: {manifest.name} v{manifest.version} (Agent API v{manifest.phantomnet_agent_version})", extra={"plugin_name": manifest.name, "plugin_version": manifest.version})
                            else:
                                self.logger.warning(f"Plugin '{manifest.name}' has unallowed permissions and was not loaded.", extra={"plugin_name": manifest.name, "requested_permissions": manifest.permissions})
                        except (ValidationError, FileNotFoundError, json.JSONDecodeError, InvalidVersion) as e:
                            self.logger.error(f"Failed to load plugin from {plugin_path}: {e}", exc_info=True, extra={"plugin_path": str(plugin_path)})
                        except Exception as e:
                            self.logger.error(f"An unexpected error occurred while loading plugin from {plugin_path}: {e}", exc_info=True, extra={"plugin_path": str(plugin_path)})
        return self.loaded_plugins

    def _check_agent_version_compatibility(self, manifest: PluginManifest) -> bool:
        """
        Checks if the plugin's phantomnet_agent_version is compatible with the agent's current version.
        A plugin is compatible if its phantomnet_agent_version is less than or equal to the agent's,
        and they share the same major version (for backward compatibility).
        """
        try:
            plugin_agent_version = Version(manifest.phantomnet_agent_version)
        except InvalidVersion:
            self.logger.error(f"Plugin '{manifest.name}' has an invalid phantomnet_agent_version format: {manifest.phantomnet_agent_version}", extra={"plugin_name": manifest.name, "version_string": manifest.phantomnet_agent_version})
            return False

        # Simple compatibility check: same major version, plugin API version <= agent API version
        if plugin_agent_version.major == self.agent_version.major and \
           plugin_agent_version <= self.agent_version:
            return True
        return False

    def _load_manifest(self, manifest_path: Path) -> PluginManifest:
        """Loads and validates a plugin's manifest file."""
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        return PluginManifest(**manifest_data)

    def _validate_permissions(self, manifest: PluginManifest) -> bool:
        """Checks if all required plugin permissions are in the allowed list."""
        for perm in manifest.permissions:
            if perm not in self.allowed_permissions:
                return False
        return True

    def _load_plugin_module(self, plugin_path: Path, manifest: PluginManifest):
        """Dynamically loads the plugin's Python module."""
        try:
            # Assuming entry is in format "module_name:function_name" or "module_name:ClassName"
            module_base_name = manifest.entry.split(':')[0]
            module_file_path = plugin_path / f"{module_base_name}.py"
            
            if not module_file_path.is_file():
                self.logger.error(f"Plugin module file not found: {module_file_path}", extra={"plugin_name": manifest.name, "module_path": str(module_file_path)})
                return None

            # Create a unique module name to avoid conflicts
            spec = importlib.util.spec_from_file_location(f"plugin_{manifest.name}_{module_base_name}", module_file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return Plugin(manifest, module)
            else:
                self.logger.error(f"Could not create module spec for plugin: {manifest.name}", extra={"plugin_name": manifest.name})
                return None
        except Exception as e:
            self.logger.error(f"Error loading plugin module '{manifest.name}': {e}", exc_info=True, extra={"plugin_name": manifest.name})
            return None