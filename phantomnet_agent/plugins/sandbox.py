import asyncio
import logging
from concurrent.futures import TimeoutError
from typing import Callable, Any, Dict, List
import time # For profiling

from utils.logger import get_logger # Use the structured logger

class PluginSandbox:
    """
    Provides a conceptual sandbox environment for executing plugin code.
    This implementation focuses on enforcing timeouts, conceptual permission checking
    based on manifest, and runtime profiling.
    """
    def __init__(self, allowed_permissions: List[str], timeout_seconds: int = 30):
        self.logger = get_logger("phantomnet_agent.plugins.sandbox")
        self.allowed_permissions = allowed_permissions
        self.timeout_seconds = timeout_seconds
        self.logger.info(f"PluginSandbox initialized with allowed permissions: {self.allowed_permissions}")

    def _check_runtime_permissions(self, manifest_permissions: List[str]) -> bool:
        """
        Conceptually checks if the plugin's requested permissions are allowed at runtime.
        This is a redundant check if PluginLoader already filters, but serves as an enforcement layer.
        """
        for perm in manifest_permissions:
            if perm not in self.allowed_permissions:
                self.logger.error(f"Plugin requested forbidden permission at runtime: {perm}", extra={"requested_permission": perm, "allowed_permissions": self.allowed_permissions})
                return False
        return True

    async def run_plugin_function(self, func: Callable, manifest_permissions: List[str], *args, **kwargs) -> Dict[str, Any]:
        """
        Executes a given plugin function within a controlled environment,
        enforcing a timeout, conceptual permission checking, and runtime profiling.
        """
        start_time = time.perf_counter()
        profiling_metrics = {
            "execution_time_seconds": 0.0,
            "cpu_usage_percent": "N/A", # Conceptual
            "memory_usage_mb": "N/A" # Conceptual
        }

        try:
            if not self._check_runtime_permissions(manifest_permissions):
                return {"status": "failed", "reason": "Plugin attempted to use forbidden permissions at runtime.", "profiling": profiling_metrics}
            
            self.logger.debug(f"Running plugin function {func.__name__} with timeout {self.timeout_seconds}s", extra={"function_name": func.__name__})
            
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout_seconds)
            else:
                # For sync functions, run them in a thread pool executor to prevent blocking the event loop
                result = await asyncio.wait_for(asyncio.to_thread(func, *args, **kwargs), timeout=self.timeout_seconds)
            
            profiling_metrics["execution_time_seconds"] = time.perf_counter() - start_time
            return {"status": "success", "result": result, "profiling": profiling_metrics}
        except TimeoutError:
            profiling_metrics["execution_time_seconds"] = time.perf_counter() - start_time
            self.logger.warning(f"Plugin function {func.__name__} timed out after {self.timeout_seconds} seconds.", extra={"function_name": func.__name__, "timeout_seconds": self.timeout_seconds})
            return {"status": "failed", "reason": f"Execution timed out after {self.timeout_seconds}s", "profiling": profiling_metrics}
        except Exception as e:
            profiling_metrics["execution_time_seconds"] = time.perf_counter() - start_time
            self.logger.error(f"Plugin function {func.__name__} raised an exception: {e}", exc_info=True, extra={"function_name": func.__name__})
            return {"status": "failed", "reason": f"Plugin execution error: {e}", "profiling": profiling_metrics}
