# backend_api/sandbox_runner.py
import docker
import os
import json
import uuid
import time
from typing import Dict, Any, Optional, List

class SandboxRunner:
    def __init__(self, docker_client=None):
        self.client = docker_client if docker_client else docker.from_env()
        self.base_image_name = "phantomnet-plugin-base"
        self.build_base_image() # Ensure base image is built on init

    def build_base_image(self):
        """Builds a base Docker image for plugins."""
        # For now, a very basic image. This should be hardened.
        dockerfile_content = """
FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true # Allow some failures for now
COPY . .
ENTRYPOINT ["python", "-u", "entry.py"]
"""
        # Create a dummy requirements.txt for the base image build
        with open("requirements.txt", "w") as f:
            f.write("pip\nsetuptools\nwheel\n") # Basic requirements

        try:
            print(f"Building base Docker image: {self.base_image_name}...")
            # Use a temporary directory for the build context
            temp_dir = f"/tmp/phantomnet_docker_build_{uuid.uuid4().hex}"
            os.makedirs(temp_dir, exist_ok=True)
            with open(os.path.join(temp_dir, "Dockerfile"), "w") as f:
                f.write(dockerfile_content)
            # Copy the dummy requirements.txt into the build context
            import shutil
            shutil.copy("requirements.txt", os.path.join(temp_dir, "requirements.txt"))

            self.client.images.build(
                path=temp_dir,
                tag=self.base_image_name,
                rm=True  # Remove intermediate containers
            )
            print(f"Successfully built base Docker image: {self.base_image_name}")
        except docker.errors.BuildError as e:
            print(f"Error building base Docker image: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during base image build: {e}")
            raise
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            # Remove the dummy requirements.txt
            if os.path.exists("requirements.txt"):
                os.remove("requirements.txt")


    def run_plugin_in_sandbox(self, plugin_name: str, plugin_path: str, manifest: Dict[str, Any], function_name: str, *args, **kwargs) -> Any:
        """
        Runs a specific function from a plugin in a Docker sandbox.
        This is a simplified example and would need extensive security hardening.
        """
        container_name = f"phantomnet-plugin-{plugin_name}-{uuid.uuid4().hex}"
        entry_point = manifest.get("entry_point", "entry.py")
        
        # Determine specific requirements for this plugin
        plugin_requirements_path = os.path.join(plugin_path, "requirements.txt")
        if os.path.exists(plugin_requirements_path):
            # Create a custom Dockerfile to install plugin-specific requirements
            plugin_dockerfile_content = f"""
FROM {self.base_image_name}
COPY {os.path.basename(plugin_requirements_path)} /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
"""
            # Build a temporary image with plugin-specific requirements
            temp_plugin_image_name = f"{self.base_image_name}-{plugin_name}-{uuid.uuid4().hex}"
            
            # Create a temporary directory for the plugin-specific image build context
            temp_build_context_dir = f"/tmp/phantomnet_plugin_build_{uuid.uuid4().hex}"
            os.makedirs(temp_build_context_dir, exist_ok=True)
            
            # Copy plugin's requirements.txt and Dockerfile into the temp build context
            import shutil
            shutil.copy(plugin_requirements_path, os.path.join(temp_build_context_dir, os.path.basename(plugin_requirements_path)))
            with open(os.path.join(temp_build_context_dir, "Dockerfile"), "w") as f:
                f.write(plugin_dockerfile_content)

            try:
                print(f"Building plugin-specific Docker image for {plugin_name}...")
                self.client.images.build(
                    path=temp_build_context_dir,
                    tag=temp_plugin_image_name,
                    rm=True
                )
                image_to_use = temp_plugin_image_name
                print(f"Successfully built plugin image: {temp_plugin_image_name}")
            except docker.errors.BuildError as e:
                print(f"Error building plugin Docker image for {plugin_name}: {e}")
                raise
            finally:
                if os.path.exists(temp_build_context_dir):
                    shutil.rmtree(temp_build_context_dir)
        else:
            image_to_use = self.base_image_name


        # Placeholder for permission enforcement:
        # Based on manifest["permissions"], configure container options (e.g., network_mode, mounts, capabilities)
        run_options: Dict[str, Any] = {
            "name": container_name,
            "detach": True, # Run in detached mode
            "network_mode": "none", # Default to no network access for security
            "read_only": True, # Default to read-only filesystem
            "environment": {
                "PLUGIN_FUNCTION": function_name,
                "PLUGIN_ARGS": json.dumps(args),
                "PLUGIN_KWARGS": json.dumps(kwargs)
            }
        }

        # Example of how permissions might influence run_options (highly simplified)
        if "network_access:scan" in manifest["permissions"] or "network_access:full" in manifest["permissions"]:
            run_options["network_mode"] = "bridge" # Allow network access
        if "file_system:read_write" in manifest["permissions"]:
            run_options["read_only"] = False
            # Needs specific volume mounts or writable directories configured
        if "system_command:full" in manifest["permissions"]:
             # This is dangerous; consider disabling or severely restricting.
             # Or using specific capabilities/seccomp profiles
            pass # No direct option here for arbitrary commands, relies on ENTRYPOINT/CMD

        # Mount the plugin directory into the container.
        # This gives the container access to the plugin's code, but the container's
        # filesystem will be mostly read-only by default (controlled by "read_only").
        # The source path must be absolute for Docker.
        abs_plugin_path = os.path.abspath(plugin_path)
        run_options["volumes"] = {abs_plugin_path: {'bind': '/app', 'mode': 'ro'}}


        container = None
        try:
            print(f"Running plugin '{plugin_name}' in sandbox...")
            container = self.client.containers.run(
                image_to_use,
                # Command to execute the entry point, passing function and args
                command=["python", "-c",
                         f"import json, importlib.util, os; "
                         f"spec = importlib.util.spec_from_file_location('{plugin_name}', os.path.join('/app', '{entry_point}')); "
                         f"module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                         f"func = getattr(module, os.environ['PLUGIN_FUNCTION']); "
                         f"result = func(*json.loads(os.environ['PLUGIN_ARGS']), **json.loads(os.environ['PLUGIN_KWARGS'])); "
                         f"print(json.dumps(result))"],
                **run_options
            )
            # Wait for container to finish and get logs
            result = container.wait(timeout=300) # 5 minutes timeout
            logs = container.logs().decode('utf-8')
            
            print(f"Sandbox logs for {plugin_name}:\n{logs}")

            # Attempt to parse the last line of logs as JSON result
            last_line = logs.strip().splitlines()[-1] if logs.strip() else ""
            if last_line.startswith("{}") and last_line.endswith("{}"):
                return json.loads(last_line)
            else:
                print(f"Warning: Could not parse plugin output as JSON: {last_line}")
                return {"_raw_output": logs, "_exit_code": result["StatusCode"]}

        except docker.errors.ContainerError as e:
            print(f"Container error for plugin '{plugin_name}': {e}")
            return {"error": str(e), "_raw_output": e.container.logs().decode('utf-8')}
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
            if 'temp_plugin_image_name' in locals() and image_to_use == temp_plugin_image_name:
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
            f.write("""
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
            f.write("""
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
        target="httpbin.org" # A public service to test network access
    )
    print(f"Sandbox run result: {result}")
    
    print("\n--- Running Test Scanner plugin (analyze_data) ---")
    result_analyze = runner.run_plugin_in_sandbox(
        plugin_name="Test Scanner",
        plugin_path="plugins/example_plugin",
        manifest=manifest_data,
        function_name="analyze_data",
        data={"some_input": "value"}
    )
    print(f"Sandbox run result (analyze_data): {result_analyze}")

    # Clean up test plugin
    import shutil
    if os.path.exists("plugins/test_plugin"):
        shutil.rmtree("plugins/test_plugin")
    if os.path.exists("requirements.txt"):
        os.remove("requirements.txt")