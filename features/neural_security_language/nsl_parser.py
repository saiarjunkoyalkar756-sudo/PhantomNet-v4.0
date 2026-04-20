import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("nsl_parser")

class NSLParser:
    """
    Neural Security Language (NSL / PNQL) Parser:
    Translates natural-language-like security scripts into actionable JSON intents.
    Supports chaining, filtering, and conditional execution.
    
    Grammar Example:
    - fetch.alerts(risk="critical").exec(action="isolate")
    - if(metric.cpu > 90).trigger(action="alert", msg="High CPU")
    - audit.system(quantum=True).verify()
    """

    def __init__(self):
        logger.info("Initializing Advanced Neural Security Language (PNQL) Parser...")

    def _extract_params(self, param_str: str) -> Dict[str, Any]:
        """Parses k='v' or k=v style parameters inside parentheses."""
        params = {}
        if not param_str:
            return params
        
        # Matches: key='value', key="value", key=123, key=True
        pairs = re.findall(r'(\w+)\s*=\s*(?:[\'"](.*?)[\'"]|(\w+))', param_str)
        for key, val1, val2 in pairs:
            val = val1 if val1 else val2
            # Type conversion
            if val.lower() == "true": val = True
            elif val.lower() == "false": val = False
            elif val.isdigit(): val = int(val)
            params[key] = val
        return params

    def parse_nsl_script(self, script: str) -> Dict[str, Any]:
        """
        Parses an NSL/PNQL string and returns an executable intent graph.
        """
        script = script.strip()
        logger.info(f"PNQL Parsing: {script}")

        # Pattern: prefix.method(params).method(params)...
        # Simplified: We'll split by dots and parse each method call
        calls = re.findall(r'(\w+)\((.*?)\)', script)
        
        if not calls:
            # Fallback for old simple regex for backward compatibility
            match = re.search(r'trigger\("(?P<trigger_action>.*?)"\)\.verify\(with="(?P<verify_with>.*?)"\)', script)
            if match:
                return {
                    "status": "parsed",
                    "intent": "legacy_trigger",
                    "action": match.group("trigger_action"),
                    "verification": match.group("verify_with")
                }
            return {"status": "failed", "reason": "No valid method calls detected."}

        intent_chain = []
        for method, params_raw in calls:
            params = self._extract_params(params_raw)
            intent_chain.append({
                "method": method,
                "params": params
            })

        # Logic Mapping
        primary_intent = intent_chain[0]["method"]
        
        # Structure the final intent object
        return {
            "status": "parsed",
            "full_chain": intent_chain,
            "primary_intent": primary_intent,
            "complexity": len(intent_chain)
        }

if __name__ == "__main__":
    parser = NSLParser()
    sample6 = 'fetch.alerts(risk="critical", limit=5).exec(action="isolate_host")'
    print(parser.parse_nsl_script(sample6))
