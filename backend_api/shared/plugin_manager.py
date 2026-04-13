# backend_api/plugin_manager.py
import json
import os
import sys
import importlib.util
from .sandbox_runner import SandboxRunner  # Import SandboxRunner


class PluginManager:
    KNOWN_PERMISSIONS = {
        "network_access:full",
        "network_access:scan",
        "file_system:read_only",
        "file_system:read_write",
        "system_command:full",
        "system_command:limited",
        "database_access:read_only",
        "database_access:read_write",
        "log_messages",
        "access_environment_variables",
        "access_secrets_manager",
    }

    def __init__(self, plugin_dir=None):
        if plugin_dir is None:
            # Construct path to be ../plugins relative to this file's directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.plugin_dir = os.path.join(base_dir, "plugins")
        else:
            self.plugin_dir = plugin_dir
        self.loaded_plugins = {}
        self.available_plugins = {}
        self.sandbox_runner = SandboxRunner()  # Instantiate SandboxRunner
        self.discover_plugins()

    def _validate_manifest(self, plugin_manifest_path):
        """Validates the structure and content of a plugin's manifest file."""
        try:
            with open(plugin_manifest_path, "r") as f:
                manifest = json.load(f)

            required_fields = [
                "name",
                "version",
                "description",
                "author",
                "entry_point",
                "type",
                "permissions",
            ]
            for field in required_fields:
                if field not in manifest:
                    raise ValueError(f"Manifest missing required field: {field}")

            # Basic type checks
            if not isinstance(manifest["name"], str) or not manifest["name"]:
                raise ValueError("Plugin 'name' must be a non-empty string.")
            if not isinstance(manifest["version"], str) or not manifest["version"]:
                raise ValueError("Plugin 'version' must be a non-empty string.")
            if not isinstance(manifest["entry_point"], str):
                raise ValueError("Plugin 'entry_point' must be a non-empty string.")
            if not isinstance(manifest["type"], str):
                raise ValueError("Plugin 'type' must be a non-empty string.")
            if not isinstance(manifest["permissions"], list):
                raise ValueError("Plugin 'permissions' must be a list.")

            # Validate requested permissions against known permissions
            for permission in manifest["permissions"]:
                if permission not in self.KNOWN_PERMISSIONS:
                    print(
                        f"Warning: Plugin '{manifest.get('name', 'Unknown')}' requests unknown permission: '{permission}'. This might indicate a typo or an unsupported feature."
                    )

            return manifest
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in manifest file: {plugin_manifest_path}")
            return None
        except ValueError as e:
            print(f"Error: Manifest validation failed for {plugin_manifest_path}: {e}")
            return None

    def discover_plugins(self):
        """
        Discovers plugins in the specified plugin directory.
        Populates self.available_plugins with validated plugin manifests.
        """
        self.available_plugins = {}
        if not os.path.isdir(self.plugin_dir):
            print(f"Warning: Plugin directory '{self.plugin_dir}' not found.")
            return

        for plugin_name in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, plugin_name)
            plugin_manifest_path = os.path.join(plugin_path, "manifest.json")

            if os.path.isdir(plugin_path) and os.path.exists(plugin_manifest_path):
                manifest = self._validate_manifest(plugin_manifest_path)
                if manifest:
                    self.available_plugins[manifest["name"]] = {
                        "path": plugin_path,
                        "manifest": manifest,
                        "status": "available",
                    }
                    print(
                        f"Discovered plugin: {manifest['name']} ({manifest['version']})"
                    )

    def load_plugin(self, plugin_name):
        """
        Marks a plugin as 'loaded' in the manager, making it available for execution.
        Actual code loading happens in the sandbox.
        """
        if plugin_name not in self.available_plugins:
            print(f"Error: Plugin '{plugin_name}' not found or not available.")
            return None

        plugin_info = self.available_plugins[plugin_name]
        if plugin_info["status"] == "loaded":
            print(f"Plugin '{plugin_name}' is already loaded.")
            return True  # Or return a reference to the loaded state if needed

        # For sandboxed execution, we don't load the module directly into this process
        # We just mark its status as loaded in the manager
        plugin_info["status"] = "loaded"
        # The sandbox_runner will ensure dependencies are handled.
        print(
            f"Plugin '{plugin_name}' marked as loaded (ready for sandboxed execution)."
        )
        return True

    def unload_plugin(self, plugin_name):
        """Unloads a plugin, removing it from loaded_plugins."""
        if (
            plugin_name in self.available_plugins
            and self.available_plugins[plugin_name]["status"] == "loaded"
        ):
            self.available_plugins[plugin_name][
                "status"
            ] = "available"  # Change status back
            print(f"Plugin '{plugin_name}' marked as unloaded.")
            return True
        print(f"Plugin '{plugin_name}' is not loaded.")
        return False

    def execute_plugin_function(
        self, plugin_name: str, function_name: str, *args, **kwargs
    ) -> dict:
        """
        Executes a specified function of a loaded plugin within its secure sandbox.
        """
        if (
            plugin_name not in self.available_plugins
            or self.available_plugins[plugin_name]["status"] != "loaded"
        ):
            return {"error": f"Plugin '{plugin_name}' not loaded or not found."}

        plugin_info = self.available_plugins[plugin_name]
        plugin_path = plugin_info["path"]
        manifest = plugin_info["manifest"]

        print(
            f"Attempting to execute function '{function_name}' from plugin '{plugin_name}' in sandbox..."
        )
        try:
            result = self.sandbox_runner.run_plugin_in_sandbox(
                plugin_name=plugin_name,
                plugin_path=plugin_path,
                manifest=manifest,
                function_name=function_name,
                *args,
                **kwargs,
            )
            return result
        except Exception as e:
            print(
                f"Error executing plugin function '{function_name}' for '{plugin_name}': {e}"
            )
            return {"error": f"Failed to execute plugin function: {str(e)}"}

    def get_plugin_info(self, plugin_name):
        """Returns detailed information about an available plugin."""
        return self.available_plugins.get(plugin_name)


# Example Usage (for testing)
if __name__ == "__main__":
    # Ensure a dummy plugin directory exists for testing
    test_plugin_dir = "plugins/test_plugin"
    if not os.path.exists(test_plugin_dir):
        os.makedirs(test_plugin_dir)
        with open(os.path.join(test_plugin_dir, "plugin.json"), "w") as f:
            f.write(
                """
{
    "name": "Test Plugin",
    "version": "1.0.0",
    "description": "A plugin for testing purposes.",
    "author": "Test Author",
    "entry_point": "test_entry.py",
    "type": "utility",
    "dependencies": ["requests"],
    "permissions": ["log_messages", "network_access:scan"]
}
"""
            )
        with open(os.path.join(test_plugin_dir, "test_entry.py"), "w") as f:
            f.write(
                """
import requests
import json
def greet(name):
    print(f"Inside sandboxed greet function, arg: {name}")
    return f"Hello from Test Plugin, {name}!"

def fetch_url(url):
    print(f"Inside sandboxed fetch_url function, arg: {url}")
    try:
        response = requests.get(url, timeout=5)
        return {"status_code": response.status_code, "content_length": len(response.text)}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
"""
            )
        with open(os.path.join(test_plugin_dir, "requirements.txt"), "w") as f:
            f.write("requests\n")

    manager = PluginManager()
    manager.discover_plugins()

    if "Test Plugin" in manager.available_plugins:
        print("\nAttempting to load 'Test Plugin'...")
        manager.load_plugin("Test Plugin")

        print("\nAttempting to execute 'greet' function from 'Test Plugin'...")
        greet_result = manager.execute_plugin_function("Test Plugin", "greet", "World")
        print(f"Sandbox run result (greet): {greet_result}")

        print(
            "\nAttempting to execute 'fetch_url' function from 'Test Plugin' (should access network)..."
        )
        fetch_result = manager.execute_plugin_function(
            "Test Plugin", "fetch_url", "http://httpbin.org/status/200"
        )
        print(f"Sandbox run result (fetch_url): {fetch_result}")

        print("\nAttempting to unload 'Test Plugin'...")
        manager.unload_plugin("Test Plugin")

    print("\nPlugins after operations:")
    for name, info in manager.available_plugins.items():
        print(f" - {name}: Status = {info['status']}")

    # Clean up test plugin
    import shutil

    if os.path.exists(test_plugin_dir):
        shutil.rmtree(test_plugin_dir)
    # The dummy requirements.txt for base image build is handled by SandboxRunner
    # No need to remove "plugins/example_plugin" as it's not created here.
