# phantomnet_agent/self_healing_ai/diagnostics_engine.py

import logging
import sys
import os
import traceback
import asyncio
import re
from collections import deque
from typing import Dict, Any, List, Tuple, Optional

from shared.platform_utils import IS_WINDOWS, IS_LINUX, IS_TERMUX
from utils.logger import get_logger

logger = get_logger(__name__)

class DiagnosticsEngine:
    """
    Collects system and program errors in real-time, parses logs, and detects common issues.
    """
    def __init__(self, log_dir: str = "logs", max_log_lines: int = 100):
        self.log_dir = log_dir
        self.max_log_lines = max_log_lines
        self.recent_errors = deque(maxlen=10) # Store recent error fingerprints
        self.issue_patterns = self._load_issue_patterns()
        self.current_process_name = os.path.basename(sys.argv[0])

    def _load_issue_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads or defines patterns for common issues.
        In a real system, this might come from a configuration file or backend.
        """
        patterns = {
            "MISSING_REQUIREMENT": {
                "regex": r"(ModuleNotFoundError|ImportError):\s*No module named\s*['"]?([\w\.]+)['"]?",
                "severity": "SEV3",
                "description": "Missing Python package dependency.",
                "fix_suggestion": "Install package: pip install {group1}"
            },
            "FILE_NOT_FOUND": {
                "regex": r"(FileNotFoundError|IOError).*:\s*\[Errno 2\] No such file or directory:\s*['"]?(.+?)['"]?",
                "severity": "SEV3",
                "description": "Required file not found.",
                "fix_suggestion": "Verify file path and existence: {group1}"
            },
            "PERMISSION_DENIED": {
                "regex": r"(PermissionError).*:\s*\[Errno 13\] Permission denied:\s*['"]?(.+?)['"]?",
                "severity": "SEV2",
                "description": "Permission denied for a file or resource.",
                "fix_suggestion": "Check file/directory permissions or run with elevated privileges: {group1}"
            },
            "NETWORK_FAILURE": {
                "regex": r"(ConnectionRefusedError|TimeoutError|requests\.exceptions\.ConnectionError):",
                "severity": "SEV2",
                "description": "Network connection could not be established or timed out.",
                "fix_suggestion": "Check network connectivity, firewall rules, and target service status."
            },
            "DATABASE_CONNECTION": {
                "regex": r"(psycopg2.OperationalError|sqlalchemy.exc.DBAPIError|redis.exceptions.ConnectionError):",
                "severity": "SEV2",
                "description": "Failed to connect to a database service.",
                "fix_suggestion": "Verify database service is running and accessible."
            },
            "INVALID_CONFIG": {
                "regex": r"(YAMLError|json.JSONDecodeError|ConfigError).*:\s*Error in configuration",
                "severity": "SEV2",
                "description": "Configuration file parsing or validation error.",
                "fix_suggestion": "Review and correct the configuration file."
            },
            "BROKEN_IMPORT_SYNTAX": {
                "regex": r"(SyntaxError):\s*invalid syntax",
                "severity": "SEV1",
                "description": "Syntax error in Python code, possibly a broken import or malformed file.",
                "fix_suggestion": "Examine recent code changes or revert to last known good version."
            },
             "EBPF_LOAD_ERROR": {
                "regex": r"Failed to initialize eBPF:.*
",
                "severity": "SEV2",
                "description": "eBPF program failed to load (Linux only).",
                "fix_suggestion": "Ensure BCC tools and kernel headers are installed and up-to-date. Verify kernel version support."
            }
            # Add more patterns for OS logs, kernel logs, etc.
        }
        return patterns

    def _parse_python_traceback(self, exc_type, exc_value, tb) -> Optional[Dict[str, Any]]:
        """Parses a Python traceback to extract error information."""
        if exc_type is None:
            return None
        
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, tb))
        error_fingerprint = f"{exc_type.__name__}: {exc_value}"
        
        details = {
            "type": exc_type.__name__,
            "message": str(exc_value),
            "traceback": tb_str,
            "fingerprint": error_fingerprint,
        }

        # Detect common issues from traceback
        for issue_type, pattern_info in self.issue_patterns.items():
            match = re.search(pattern_info["regex"], tb_str, re.IGNORECASE | re.DOTALL)
            if match:
                details["detected_issue_type"] = issue_type
                details["issue_description"] = pattern_info["description"]
                details["severity"] = pattern_info["severity"]
                
                fix_suggestion = pattern_info["fix_suggestion"]
                for i in range(1, len(match.groups()) + 1):
                    fix_suggestion = fix_suggestion.replace(f"{{group{i}}}", match.group(i))
                details["fix_suggestion"] = fix_suggestion
                break
        
        return details

    def _monitor_log_file(self, file_path: str):
        """Monitors a log file for new errors."""
        try:
            with open(file_path, 'r') as f:
                f.seek(0, 2) # Go to the end of the file
                while True:
                    line = f.readline()
                    if not line:
                        asyncio.sleep(0.1) # Wait a bit if no new line
                        continue
                    
                    # Basic error detection in log lines
                    if "error" in line.lower() or "exception" in line.lower() or "fail" in line.lower():
                        # This is very basic. A real parser would check for multiline errors.
                        # For now, just detect single line errors.
                        logger.debug(f"Detected potential error in log: {line.strip()}")
                        # Here, we'd feed this to error_classifier
        except FileNotFoundError:
            logger.warning(f"Log file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error monitoring log file {file_path}: {e}")

    async def _monitor_system_logs(self):
        """Monitors system-wide logs based on OS."""
        if IS_LINUX:
            # Example: monitor journald for relevant services
            # This would require subprocess calls to journalctl
            logger.info("Monitoring Linux system logs (journalctl - simulated)...")
            # Example: subprocess.Popen(['journalctl', '-f', '-u', 'phantomnet-agent.service'])
            await asyncio.sleep(60) # Simulate monitoring
        elif IS_WINDOWS:
            # Example: monitor Windows Event Log
            # Requires pywin32, or powershell commands
            logger.info("Monitoring Windows Event Logs (simulated)...")
            await asyncio.sleep(60) # Simulate monitoring
        elif IS_TERMUX:
            # Termux often relies on app-specific logs or basic logcat
            logger.info("Monitoring Termux application logs (simulated)...")
            await asyncio.sleep(60) # Simulate monitoring
        else:
            logger.warning("System log monitoring not implemented for this OS.")

    async def run_diagnostics(self):
        """Main loop for running continuous diagnostics."""
        logger.info("DiagnosticsEngine starting...")
        
        # Monitor Python errors directly
        sys.excepthook = self._handle_unhandled_exception

        # Monitor local agent log files
        # Assuming agent's main log file is in log_dir
        # You'd have to identify all relevant log files here
        # self_healing_controller will manage scheduling this correctly

        # Example: monitor its own log file
        agent_log_path = os.path.join(self.log_dir, f"{self.current_process_name}.log")
        # In a real async setup, this needs to be non-blocking or in a separate thread/process.
        # For simplicity, we'll just periodically check for new error patterns here for now.
        
        # Start system log monitoring as a background task
        asyncio.create_task(self._monitor_system_logs())

        while True:
            # Placeholder for real-time log parsing or polling if other methods fail
            # The actual log monitoring needs to be event-driven or robustly threaded
            await asyncio.sleep(5) # Simulate work

    def _handle_unhandled_exception(self, exc_type, exc_value, tb):
        """Custom exception hook to catch unhandled Python exceptions."""
        error_details = self._parse_python_traceback(exc_type, exc_value, tb)
        if error_details:
            logger.error(f"Unhandled Python Exception Detected: {error_details['fingerprint']}", extra=error_details)
            self.recent_errors.append(error_details)
        
        # Call default exception hook to ensure error is still printed to console/stderr
        sys.__excepthook__(exc_type, exc_value, tb)

    def get_recent_errors(self) -> List[Dict[str, Any]]:
        """Returns a list of recent error details."""
        return list(self.recent_errors)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running DiagnosticsEngine example...")
    engine = DiagnosticsEngine()
    
    # Example: Trigger a missing module error
    def trigger_missing_module():
        try:
            import non_existent_module_phantomnet_test
        except ImportError:
            exc_type, exc_value, tb = sys.exc_info()
            engine._handle_unhandled_exception(exc_type, exc_value, tb)

    # Example: Trigger a file not found error
    def trigger_file_not_found():
        try:
            with open("non_existent_file_phantomnet_test.txt", "r") as f:
                pass
        except FileNotFoundError:
            exc_type, exc_value, tb = sys.exc_info()
            engine._handle_unhandled_exception(exc_type, exc_value, tb)

    async def run_example():
        await engine.run_diagnostics()
        trigger_missing_module()
        trigger_file_not_found()
        
        # Give some time for diagnostics to potentially log/process
        await asyncio.sleep(1)
        
        print("\n--- Recent Errors ---")
        for err in engine.get_recent_errors():
            print(f"Type: {err.get('type')}, Issue: {err.get('detected_issue_type')}, Severity: {err.get('severity')}")
            print(f"Message: {err.get('message')}")
            print(f"Suggestion: {err.get('fix_suggestion')}")
            print("-" * 20)

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("DiagnosticsEngine example stopped.")
