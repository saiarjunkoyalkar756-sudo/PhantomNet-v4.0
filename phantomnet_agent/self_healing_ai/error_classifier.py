# phantomnet_agent/self_healing_ai/error_classifier.py

import logging
from typing import Dict, Any, Optional, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

class ErrorClassifier:
    """
    Categorizes errors based on severity, predicts root cause, and suggests fix steps.
    Uses a hybrid approach of rule-based logic and (conceptual) ML.
    """
    def __init__(self):
        self.severity_mapping = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
            "INFO": 5
        }
        self.reverse_severity_mapping = {v: k for k, v in self.severity_mapping.items()}
        
        # Conceptual ML model (placeholder)
        self.ml_model = self._load_ml_model()

    def _load_ml_model(self):
        """
        Loads a pre-trained ML model for error classification if available.
        For now, this is a placeholder.
        """
        logger.info("Conceptual: Loading ML model for error classification...")
        # In a real scenario, this would load a model trained on past errors and fixes.
        return None

    def classify_error(self, error_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifies an error, predicts root cause, and suggests fix steps.
        Augments the error_details dictionary.
        """
        severity = error_details.get("severity", "LOW")
        issue_type = error_details.get("detected_issue_type", "UNKNOWN")
        message = error_details.get("message", "")
        
        # --- Rule-Based Classification ---
        # Prioritize rule-based if specific patterns are matched by diagnostics_engine
        if "detected_issue_type" in error_details:
            logger.debug(f"Rule-based classification: {issue_type} (Severity: {severity})")
            return self._augment_error_details(error_details)
        
        # Fallback to general rules if diagnostics_engine didn't catch it
        if "permission denied" in message.lower():
            severity = "SEV2"
            issue_type = "PERMISSION_DENIED"
        elif "connection refused" in message.lower() or "timeout" in message.lower():
            severity = "SEV2"
            issue_type = "NETWORK_FAILURE"
        elif "no module named" in message.lower() or "importerror" in message.lower():
            severity = "SEV3"
            issue_type = "MISSING_REQUIREMENT"
        
        # --- ML-Based Classification (Conceptual) ---
        if self.ml_model:
            # Conceptual: Extract features from error_details (e.g., embeddings of traceback)
            # prediction = self.ml_model.predict(features)
            # if prediction > some_threshold:
            #     severity = self._map_ml_severity(prediction_severity)
            #     issue_type = self._map_ml_issue_type(prediction_issue_type)
            logger.debug("Conceptual: Running ML-based error classification...")
            ml_confidence = 0.75 # Placeholder
            if ml_confidence > 0.6: # If ML has high confidence
                # For demonstration, let's say ML confirms previous rule-based or provides new insight
                if issue_type == "UNKNOWN":
                    issue_type = "ML_PREDICTED_ISSUE"
                error_details["ml_confidence"] = ml_confidence
        
        error_details["classified_severity"] = severity
        error_details["classified_issue_type"] = issue_type
        error_details["root_cause_prediction"] = self._predict_root_cause(issue_type, message)
        error_details["suggested_fix_steps"] = self._suggest_fix_steps(issue_type, message)

        return self._augment_error_details(error_details)

    def _augment_error_details(self, error_details: Dict[str, Any]) -> Dict[str, Any]:
        """Adds additional details or refines existing ones."""
        # Ensure severity is in SEV1, SEV2, SEV3 format
        original_severity = error_details.get("severity")
        if original_severity and original_severity.startswith("SEV"):
             error_details["classified_severity"] = original_severity
        else: # Map general severities to SEV levels if not already
            if "CRITICAL" in original_severity: error_details["classified_severity"] = "SEV1"
            elif "HIGH" in original_severity: error_details["classified_severity"] = "SEV2"
            elif "MEDIUM" in original_severity: error_details["classified_severity"] = "SEV3"
            elif "LOW" in original_severity: error_details["classified_severity"] = "SEV3" # Low to SEV3 for active remediation
            else: error_details["classified_severity"] = "SEV3" # Default to SEV3

        # Default root cause and fix if not set by diagnostics_engine
        if "root_cause_prediction" not in error_details:
            error_details["root_cause_prediction"] = self._predict_root_cause(
                error_details.get("classified_issue_type", "UNKNOWN"), 
                error_details.get("message", "")
            )
        if "suggested_fix_steps" not in error_details:
            error_details["suggested_fix_steps"] = self._suggest_fix_steps(
                error_details.get("classified_issue_type", "UNKNOWN"), 
                error_details.get("message", "")
            )
        return error_details

    def _predict_root_cause(self, issue_type: str, message: str) -> str:
        """Predicts the root cause based on issue type and message."""
        if issue_type == "MISSING_REQUIREMENT":
            match = re.search(r"No module named\s*['"]?([\w\.]+)['"]?", message)
            if match:
                return f"Python package '{match.group(1)}' is not installed."
            return "A required Python package is missing."
        elif issue_type == "PERMISSION_DENIED":
            return "Insufficient privileges or incorrect file permissions."
        elif issue_type == "NETWORK_FAILURE":
            return "External network service is unreachable or blocked."
        elif issue_type == "DATABASE_CONNECTION":
            return "Database service is down or inaccessible."
        elif issue_type == "INVALID_CONFIG":
            return "Configuration file is malformed or contains invalid values."
        elif issue_type == "EBPF_LOAD_ERROR":
            return "eBPF dependencies (kernel headers, BCC) are not correctly set up for the Linux kernel."
        return "Unknown root cause. Further investigation needed."

    def _suggest_fix_steps(self, issue_type: str, message: str) -> List[str]:
        """Suggests concrete steps to fix the detected issue."""
        if "fix_suggestion" in error_details: # From diagnostics_engine pattern
            return [error_details["fix_suggestion"]]
        
        if issue_type == "MISSING_REQUIREMENT":
            match = re.search(r"No module named\s*['"]?([\w\.]+)['"]?", message)
            package_name = match.group(1) if match else "missing_package"
            return [f"Attempt to install the missing Python package: pip install {package_name}"]
        elif issue_type == "PERMISSION_DENIED":
            return ["Check file/directory permissions (chmod, icacls).", "Ensure the agent is running with appropriate user context or elevated privileges."]
        elif issue_type == "NETWORK_FAILURE":
            return ["Ping target host to check connectivity.", "Verify firewall rules (ufw, Windows Firewall).", "Check if target service is running."]
        elif issue_type == "DATABASE_CONNECTION":
            return ["Verify database server status (systemctl status postgresql).", "Check database connection strings in configuration.", "Ensure network access to the database port."]
        elif issue_type == "INVALID_CONFIG":
            return ["Review the agent's configuration file for syntax errors.", "Validate configuration against schema if available.", "Restore configuration from backup."]
        elif issue_type == "EBPF_LOAD_ERROR":
            return ["Check if Linux kernel headers are installed and match the running kernel (sudo apt install linux-headers-$(uname -r)).", "Verify BCC installation (sudo apt install bpfcc-tools)."]
        return ["Consult logs for more details.", "Restart affected component or agent.", "Report to central management."]

    def send_error_signature_to_backend(self, error_details: Dict[str, Any]):
        """
        Conceptual function to send error fingerprint and solution to backend for learning.
        """
        logger.info(f"Conceptual: Sending error signature to backend for learning: {error_details.get('fingerprint')}")
        # In a real system, this would make an API call to the backend.
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running ErrorClassifier example...")
    
    classifier = ErrorClassifier()

    sample_error = {
        "type": "ImportError",
        "message": "No module named 'requests'",
        "traceback": "...",
        "fingerprint": "ImportError: No module named 'requests'",
        "detected_issue_type": "MISSING_REQUIREMENT",
        "severity": "SEV3"
    }
    classified_error = classifier.classify_error(sample_error)
    print("\n--- Classified Error ---")
    print(classified_error)
    
    unclassified_error = {
        "type": "PermissionError",
        "message": "[Errno 13] Permission denied: '/var/log/phantomnet.log'",
        "traceback": "...",
        "fingerprint": "PermissionError: [Errno 13] Permission denied",
    }
    classified_error_2 = classifier.classify_error(unclassified_error)
    print("\n--- Classified Error 2 ---")
    print(classified_error_2)
