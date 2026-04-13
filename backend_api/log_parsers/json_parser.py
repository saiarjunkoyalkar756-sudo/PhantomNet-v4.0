import json
from typing import Dict, Any, Tuple, Optional, List
from .base_parser import BaseLogParser


class JsonLogParser(BaseLogParser):
    """
    A log parser specifically for JSON formatted log entries.
    """

    def parse(
        self, log_entry: str, source: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        try:
            parsed_data = json.loads(log_entry)
            return parsed_data, log_entry
        except json.JSONDecodeError:
            # If it's not valid JSON, return as a plaintext message
            return {"message": log_entry}, log_entry

    @property
    def name(self) -> str:
        return "json_parser"

    @property
    def supported_types(self) -> List[str]:
        return ["json", "application/json"]
