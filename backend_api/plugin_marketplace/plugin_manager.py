import os
import json
import logging
import importlib.util
import sys

logger = logging.getLogger(__name__)


class PluginManager:
    def __init__(self, plugin_dir: str):
        self.plugin_dir = plugin_dir
        self.plugins = {}  # Stores loaded plugin objects/metadata

    def load_installed_plugins(self):
        """
        Scans the plugin directory and loads metadata for installed plugins.
        """
        logger.info(f"Scanning for plugins in {self.plugin_dir}...")
        for plugin_id in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, plugin_id)
            manifest_path = os.path.join(plugin_path, "manifest.json")
            if os.path.isdir(plugin_path) and os.path.exists(manifest_path):
                try:
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                    self.plugins[plugin_id] = {
                        "id": plugin_id,
                        "manifest": manifest,
                        "status": "disabled",  # Default status
                        "instance": None,  # Placeholder for loaded module instance
                    }
                    logger.info(
                        f"Loaded metadata for plugin: {manifest.get('name', plugin_id)}"
                    )
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid manifest.json for plugin {plugin_id}: {e}")
                except Exception as e:
                    logger.error(
                        f"Error loading plugin metadata for {plugin_id}: {e}",
                        exc_info=True,
                    )
        logger.info(f"Found {len(self.plugins)} plugins.")

    def register_plugin(self, manifest: dict, filename: str = None):
        """
        Registers a new plugin by its manifest.
        In a real scenario, this would involve unpacking, validation, etc.
        """
        plugin_id = manifest.get("id") or str(
            uuid.uuid4()
        )  # Generate ID if not present
        if plugin_id in self.plugins:
            logger.warning(f"Plugin {plugin_id} already registered. Updating manifest.")

        # For simplicity, we assume the plugin is a directory with a manifest.json
        # and an entry point script.
        # This function should ensure the plugin directory structure is set up.

        self.plugins[plugin_id] = {
            "id": plugin_id,
            "manifest": manifest,
            "status": "disabled",
            "instance": None,
        }
        logger.info(f"Plugin '{manifest.get('name', plugin_id)}' registered.")
        return True

    def list_plugins(self):
        """
        Returns a list of all registered plugins with their status.
        """
        return [
            {"id": p["id"], "name": p["manifest"].get("name"), "status": p["status"]}
            for p in self.plugins.values()
        ]

    def get_plugin(self, plugin_id: str):
        """
        Returns details for a specific plugin.
        """
        return self.plugins.get(plugin_id)

    def enable_plugin(self, plugin_id: str):
        """
        Enables a plugin, loading its entry point.
        """
        plugin_info = self.plugins.get(plugin_id)
        if not plugin_info:
            return False

        if plugin_info["status"] == "enabled":
            logger.info(f"Plugin {plugin_id} is already enabled.")
            return True

        # Placeholder for sandbox execution and actual module loading
        try:
            # In a real system, this would happen in a sandboxed environment
            # For this code, we assume plugin_id is the directory name
            entry_point_script = plugin_info["manifest"].get("entry_point")
            if not entry_point_script:
                logger.error(f"Plugin {plugin_id} manifest missing 'entry_point'.")
                return False

            plugin_path = os.path.join(self.plugin_dir, plugin_id, entry_point_script)
            if not os.path.exists(plugin_path):
                logger.error(
                    f"Plugin {plugin_id} entry point not found at {plugin_path}."
                )
                return False

            # This is a very basic import, NOT sandboxed.
            # Real plugin systems use dedicated environments, process isolation, etc.
            spec = importlib.util.spec_from_file_location(plugin_id, plugin_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_id] = module
            spec.loader.exec_module(module)

            # Assuming the plugin's entry point defines a class or function to initialize
            if hasattr(module, "initialize_plugin"):
                plugin_info["instance"] = module.initialize_plugin()
                logger.info(f"Plugin {plugin_id} initialized.")
            else:
                plugin_info["instance"] = module  # Just load the module
                logger.warning(
                    f"Plugin {plugin_id} has no 'initialize_plugin' function."
                )

            plugin_info["status"] = "enabled"
            logger.info(f"Plugin {plugin_id} enabled successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_id}: {e}", exc_info=True)
            return False

    def disable_plugin(self, plugin_id: str):
        """
        Disables a plugin, unloading its entry point.
        """
        plugin_info = self.plugins.get(plugin_id)
        if not plugin_info:
            return False

        if plugin_info["status"] == "disabled":
            logger.info(f"Plugin {plugin_id} is already disabled.")
            return True

        # Placeholder for unloading/cleaning up resources
        if plugin_info["instance"]:
            # In a real system, this would trigger a cleanup method on the plugin instance
            logger.info(f"Plugin {plugin_id} instance cleaned up (placeholder).")

        # Remove from sys.modules if it was added
        if plugin_id in sys.modules:
            del sys.modules[plugin_id]

        plugin_info["status"] = "disabled"
        plugin_info["instance"] = None
        logger.info(f"Plugin {plugin_id} disabled successfully.")
        return True

    # Placeholder for sandbox runner and hot reload mechanisms
    def run_in_sandbox(self, plugin_id: str, function_name: str, *args, **kwargs):
        logger.info(
            f"Running '{function_name}' for plugin '{plugin_id}' in sandbox (placeholder)."
        )
        # This would involve process isolation, resource limits, etc.
        if plugin_id in self.plugins and self.plugins[plugin_id]["instance"]:
            instance = self.plugins[plugin_id]["instance"]
            if hasattr(instance, function_name):
                return getattr(instance, function_name)(*args, **kwargs)
        return {"error": "Plugin not active or function not found"}

    def hot_reload_plugin(self, plugin_id: str):
        logger.info(f"Hot-reloading plugin '{plugin_id}' (placeholder).")
        # This would involve disabling, re-loading, and re-enabling
        self.disable_plugin(plugin_id)
        self.enable_plugin(plugin_id)
        return True
