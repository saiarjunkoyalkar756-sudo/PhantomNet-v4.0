# backend_api/sandbox_runner.py
import docker
import os
import json
import uuid
import time
from typing import Dict, Any, Optional, List


# --- Mock Docker Client for environments without Docker daemon ---
class MockContainer:
    def __init__(self, name, image, command, options):
        self.name = name
        self.image = image
        self.command = command
        self.options = options
        self._logs = (
            f"Mock container '{self.name}' run with image '{self.image}' and command: {self.command}\n"
            f"Options: {self.options}\n"
            f"Simulated plugin output: {{'mock_result': 'success', 'plugin_name': '{self.name}'}}"
        )
        print(f"Mocking: Container '{self.name}' started.")

    def wait(self, timeout=300):
        print(f"Mocking: Container '{self.name}' waited for {timeout} seconds.")
        return {"StatusCode": 0}

    def logs(self):
        print(f"Mocking: Returning logs for container '{self.name}'.")
        return self._logs.encode("utf-8")

    def stop(self):
        print(f"Mocking: Container '{self.name}' stopped.")

    def remove(self):
        print(f"Mocking: Container '{self.name}' removed.")


class MockImage:
    def __init__(self, name):
        self.name = name

    def remove(self):
        print(f"Mocking: Image '{self.name}' removed.")


class MockImages:
    def build(self, path, tag, rm):
        print(f"Mocking: Building image '{tag}' from path '{path}'.")
        return [MockImage(tag)], None  # Return a dummy image and no build logs

    def remove(self, image_name):
        print(f"Mocking: Image '{image_name}' removed.")


class MockContainers:
    def run(self, image, command, **kwargs):
        name = kwargs.get("name", "mock_container")
        print(f"Mocking: Running container '{name}' with image '{image}'.")
        return MockContainer(name, image, command, kwargs)


class MockDockerClient:
    def __init__(self):
        print(
            "Mocking: Initializing MockDockerClient. No real Docker daemon connected."
        )
        self.images = MockImages()
        self.containers = MockContainers()
        self.from_env_succeeded = False  # Flag to indicate that mocking is active


class SandboxRunner:
    def __init__(self):
        self.client = None
        self.from_env_succeeded = False
        self.base_image_name = "phantomnet-plugin-base"

    def _init_client(self):
        if self.client is None:
            try:
                self.client = docker.from_env()
                self.from_env_succeeded = True
                print("Connected to Docker daemon.")
                self.build_base_image()
            except (docker.errors.DockerException, ConnectionError) as e:
                print(
                    f"Warning: Could not connect to Docker daemon: {e}. Using MockDockerClient."
                )
                self.client = MockDockerClient()
                self.from_env_succeeded = False


    def build_base_image(self, force_build=False):
        self._init_client()
        if not self.from_env_succeeded:
            print(
                "Mocking: Skipping base Docker image build as MockDockerClient is in use."
            )
            return

        # Check if image already exists
        if not force_build:
            try:
                self.client.images.get(self.base_image_name)
                print(
                    f"Base Docker image '{self.base_image_name}' already exists. Skipping build."
                )
                return
            except docker.errors.ImageNotFound:
                pass  # Image does not exist, proceed with build

    def run_plugin_in_sandbox(
        self,
        plugin_name: str,
        plugin_path: str,
        manifest: Dict[str, Any],
        function_name: str,
        *args,
        **kwargs,
    ) -> Any:
        self._init_client()
        if not self.from_env_succeeded:
            print(
                f"Mocking: Running plugin '{plugin_name}' function '{function_name}' with MockDockerClient."
            )
            # Simulate plugin logic and return a mock result
            mock_output = {
                "is_anomaly": False,
                "anomaly_score": 0.1,
                "suggested_action": "Mocked Monitor",
                "details": f"Simulated execution of {function_name} for {plugin_name}",
                "simulated_logs": f"Plugin '{plugin_name}' (mocked) says: Hello from simulated sandbox!",
            }
            return mock_output

        """
        Runs a specific function from a plugin in a Docker sandbox.
        This is a simplified example and would need extensive security hardening.
        """
        container_name = f"phantomnet-plugin-{plugin_name}-{uuid.uuid4().hex}"
        entry_point = manifest.get("entry_point", "entry.py")

        # Determine specific requirements for this plugin
        plugin_requirements_path = os.path.abspath(
            os.path.join(plugin_path, "requirements.txt")
        )  # Use absolute path
        image_to_use = self.base_image_name
        temp_plugin_image_name = None

        if os.path.exists(plugin_requirements_path):
            # Create a custom Dockerfile to install plugin-specific requirements
            plugin_dockerfile_content = f"""
FROM {self.base_image_name}
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt || true
COPY . /app
"""
            # Build a temporary image with plugin-specific requirements
            temp_plugin_image_name = (
                f"{self.base_image_name}-{plugin_name}-{uuid.uuid4().hex}"
            )

            # Create a temporary directory for the plugin-specific image build context
            temp_build_context_dir = f"/tmp/phantomnet_plugin_build_{uuid.uuid4().hex}"
            os.makedirs(temp_build_context_dir, exist_ok=True)

            # Copy plugin's requirements.txt and Dockerfile into the temp build context
            import shutil

            shutil.copy(
                plugin_requirements_path,
                os.path.join(temp_build_context_dir, "requirements.txt"),
            )
            with open(os.path.join(temp_build_context_dir, "Dockerfile"), "w") as f:
                f.write(plugin_dockerfile_content)

            try:
                print(f"Building plugin-specific Docker image for {plugin_name}...")
                self.client.images.build(
                    path=temp_build_context_dir, tag=temp_plugin_image_name, rm=True
                )
                image_to_use = temp_plugin_image_name
                print(f"Successfully built plugin image: {temp_plugin_image_name}")
            except docker.errors.BuildError as e:
                print(f"Error building plugin Docker image for {plugin_name}: {e}")
                raise
            finally:
                if os.path.exists(temp_build_context_dir):
                    shutil.rmtree(temp_build_context_dir)

        # Placeholder for permission enforcement:
        # Based on manifest["permissions"], configure container options (e.g., network_mode, mounts, capabilities)
        run_options: Dict[str, Any] = {
            "name": container_name,
            "detach": True,  # Run in detached mode
            "network_mode": "none",  # Default to no network access for security
            "read_only": True,  # Default to read-only filesystem
            "environment": {
                "PLUGIN_FUNCTION": function_name,
                "PLUGIN_ARGS": json.dumps(args),
                "PLUGIN_KWARGS": json.dumps(kwargs),
            },
        }

        # Example of how permissions might influence run_options (highly simplified)
        if (
            "network_access:scan" in manifest["permissions"]
            or "network_access:full" in manifest["permissions"]
        ):
            run_options["network_mode"] = "bridge"  # Allow network access
        if "file_system:read_write" in manifest["permissions"]:
            run_options["read_only"] = False
            # Needs specific volume mounts or writable directories configured
        if "system_command:full" in manifest["permissions"]:
            # This is dangerous; consider disabling or severely restricting.
            # Or using specific capabilities/seccomp profiles
            pass  # No direct option here for arbitrary commands, relies on ENTRYPOINT/CMD

        # Mount the plugin directory into the container.
        # This gives the container access to the plugin's code, but the container's
        # filesystem will be mostly read-only by default (controlled by "read_only").
        # The source path must be absolute for Docker.
        abs_plugin_path = os.path.abspath(plugin_path)
        run_options["volumes"] = {abs_plugin_path: {"bind": "/app", "mode": "ro"}}

        container = None
        try:
            print(f"Running plugin '{plugin_name}' in sandbox...")
            container = self.client.containers.run(
                image_to_use,
                # Command to execute the entry point, passing function and args
                command=[
                    "python",
                    "-c",
                    f"import json, importlib.util, os; "
                    f"spec = importlib.util.spec_from_file_location('{plugin_name}', os.path.join('/app', '{entry_point}')); "
                    f"module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                    f"func = getattr(module, os.environ['PLUGIN_FUNCTION']); "
                    f"result = func(*json.loads(os.environ['PLUGIN_ARGS']), **json.loads(os.environ['PLUGIN_KWARGS'])); "
                    f"print(json.dumps(result))",
                ],
                **run_options,
            )
            # Wait for container to finish and get logs
            result = container.wait(timeout=300)  # 5 minutes timeout
            logs = container.logs().decode("utf-8")

            print(f"Sandbox logs for {plugin_name}:\n{logs}")

            # Attempt to parse the last line of logs as JSON result
            last_line = logs.strip().splitlines()[-1] if logs.strip() else ""
            if last_line.startswith("{") and last_line.endswith(
                "}"
            ):  # Check for proper JSON string
                return json.loads(last_line)
            else:
                print(f"Warning: Could not parse plugin output as JSON: {last_line}")
                return {"_raw_output": logs, "_exit_code": result["StatusCode"]}

        except docker.errors.ContainerError as e:
            print(f"Container error for plugin '{plugin_name}': {e}")
            return {"error": str(e), "_raw_output": e.container.logs().decode("utf-8")}
        except docker.errors.ImageNotFound as e:
            print(f"Image not found for plugin '{plugin_name}': {e}")
            return {"error": f"Docker image not found: {e}"}
        except Exception as e:
            print(f"Error running plugin '{plugin_name}' in sandbox: {e}")
            return {"error": str(e)}
        finally:
            if container:
                print(f"Stopping and removing container {container_name}...")
                try:
                    container.stop()
                    container.remove()
                except Exception as e:
                    print(f"Error cleaning up container {container_name}: {e}")
            # Clean up temporary plugin-specific image if it was built
            if temp_plugin_image_name and image_to_use == temp_plugin_image_name:
                try:
                    self.client.images.remove(image_to_use)
                    print(f"Removed temporary plugin image: {image_to_use}")
                except Exception as e:
                    print(f"Error removing temporary plugin image {image_to_use}: {e}")


# Example usage for testing the SandboxRunner
if __name__ == "__main__":
    # Ensure the example plugin directory exists
    if not os.path.exists("plugins/example_plugin"):
        os.makedirs("plugins/example_plugin")
        with open("plugins/example_plugin/manifest.json", "w") as f:
            f.write(
                """
{
    "name": "Test Scanner",
    "version": "0.1.0",
    "description": "A test scanner plugin.",
    "author": "PhantomNet",
    "entry_point": "entry.py",
    "type": "scanner",
    "dependencies": ["requests"],
    "permissions": ["network_access:scan", "log_messages"],
    "sandbox_config": {"isolation_level": "medium"}
}
"""
            )
        with open("plugins/example_plugin/entry.py", "w") as f:
            f.write(
                """
import requests
import json
def scan_target(target):
    print(f"Performing a dummy scan on {target}")
    try:
        response = requests.get(f"http://{target}", timeout=2)
        status = response.status_code
    except requests.exceptions.RequestException as e:
        status = f"Error: {e}"
    
    # This JSON output will be captured by the sandbox runner
    return {"scan_result": f"Target {target} status: {status}", "data": "some_scanned_data"}

def analyze_data(data):
    return {"analysis_result": f"Analyzed: {data}"}

if __name__ == "__main__":
    # Example for local testing, not used by sandbox
    print(json.dumps(scan_target("example.com")))
"""
            )
        with open("plugins/example_plugin/requirements.txt", "w") as f:
            f.write("requests\n")

    runner = SandboxRunner()

    print("\n--- Running Test Scanner plugin ---")
    with open("plugins/example_plugin/manifest.json", "r") as f:
        manifest_data = json.load(f)

    # Test a function call
    result = runner.run_plugin_in_sandbox(
        plugin_name="Test Scanner",
        plugin_path="plugins/example_plugin",
        manifest=manifest_data,
        function_name="scan_target",
        target="httpbin.org",  # A public service to test network access
    )
    print(f"Sandbox run result: {result}")

    print("\n--- Running Test Scanner plugin (analyze_data) ---")
    result_analyze = runner.run_plugin_in_sandbox(
        plugin_name="Test Scanner",
        plugin_path="plugins/example_plugin",
        manifest=manifest_data,
        function_name="analyze_data",
        data={"some_input": "value"},
    )
    print(f"Sandbox run result (analyze_data): {result_analyze}")

    # Clean up test plugin
    import shutil

    if os.path.exists("plugins/test_plugin"):
        shutil.rmtree("plugins/test_plugin")
    if os.path.exists("requirements.txt"):
        os.remove("requirements.txt")
