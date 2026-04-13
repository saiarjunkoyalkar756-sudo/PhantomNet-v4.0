import json
from typing import Dict, Any, Tuple, Optional, List
from ..log_parsers.base_parser import BaseLogParser

class AWSCloudTrailParser(BaseLogParser):
    """
    Parses AWS CloudTrail logs.
    CloudTrail logs are delivered as JSON objects.
    """

    @property
    def name(self) -> str:
        return "aws_cloudtrail_parser"

    @property
    def supported_types(self) -> List[str]:
        return ["aws-cloudtrail", "cloudtrail"]

    def parse(
        self, log_entry: str, source: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Parses a JSON string representing an AWS CloudTrail event.

        Args:
            log_entry: The raw log entry string (should be a JSON object).
            source: The source of the log.

        Returns:
            A tuple containing:
            - A dictionary representing the structured, parsed data.
            - The original raw log entry string.
        """
        try:
            # CloudTrail logs are JSON, so we just load the string
            parsed_data = json.loads(log_entry)
            
            # You might want to do some normalization or extraction here
            # For example, flatten the structure or pull out key fields
            # For now, we'll return the full parsed data
            
            return parsed_data, log_entry
        except json.JSONDecodeError:
            # If it's not a valid JSON, we can't parse it with this parser
            return {}, log_entry
        except Exception as e:
            # Handle other potential errors
            print(f"Error parsing AWS CloudTrail log: {e}")
            return {}, log_entry
