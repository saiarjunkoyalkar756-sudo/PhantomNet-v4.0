
import re
from typing import Dict, Any, Tuple, Optional, List
from ..log_parsers.base_parser import BaseLogParser


class AccessLogParser(BaseLogParser):
    """
    Parses common web server access log formats (e.g., Apache combined log format).
    Example format:
    127.0.0.1 - user [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326
    """

    # Regex for Apache combined log format
    # This regex is a simplified version and might need adjustments for all edge cases
    _log_pattern = re.compile(
        r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - (\S+) \[([^\]]+)\] "(\S+)\s(\S+)\s(\S+)" (\d{3}) (\d+|-)'
    )

    @property
    def name(self) -> str:
        return "access_log_parser"

    @property
    def supported_types(self) -> List[str]:
        return ["apache_access", "nginx_access", "web_access_log"]

    def parse(
        self,
        log_entry: str,
        source: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        match = self._log_pattern.match(log_entry)
        if match:
            (
                ip_address,
                identd,
                timestamp,
                method,
                path,
                protocol,
                status,
                size,
            ) = match.groups()

            parsed_data = {
                "ip_address": ip_address,
                "identd": identd,
                "timestamp": timestamp,
                "method": method,
                "path": path,
                "protocol": protocol,
                "status": int(status),
                "size": int(size) if size != "-" else 0,
                "message": log_entry,  # Keep original log as message
                "type": "web_access_log",
                "source": source if source else self.name
            }
            return parsed_data, log_entry
        else:
            # If parsing fails, return the log entry as a simple message
            return {"message": log_entry, "type": "unparsed_access_log", "source": source if source else self.name}, log_entry


if __name__ == "__main__":
    parser = AccessLogParser()

    # Test cases
    log_line_1 = '192.168.1.10 - user1 [24/Aug/2023:14:30:01 +0000] "GET /index.html HTTP/1.1" 200 1234'
    log_line_2 = '10.0.0.5 - - [24/Aug/2023:14:31:05 +0000] "POST /api/data HTTP/1.1" 500 0'
    log_line_3 = 'invalid log line without proper format'
    log_line_4 = '172.16.0.1 - admin [01/Jan/2024:08:00:00 -0500] "PUT /admin/update HTTP/1.0" 403 500'

    print("--- Test Log Line 1 ---")
    parsed_data_1, _ = parser.parse(log_line_1, source="nginx_access")
    print(parsed_data_1)
    assert parsed_data_1["ip_address"] == "192.168.1.10"
    assert parsed_data_1["status"] == 200
    assert parsed_data_1["size"] == 1234
    assert parsed_data_1["source"] == "nginx_access"

    print("\n--- Test Log Line 2 ---")
    parsed_data_2, _ = parser.parse(log_line_2)
    print(parsed_data_2)
    assert parsed_data_2["ip_address"] == "10.0.0.5"
    assert parsed_data_2["status"] == 500
    assert parsed_data_2["size"] == 0

    print("\n--- Test Log Line 3 (Invalid) ---")
    parsed_data_3, _ = parser.parse(log_line_3)
    print(parsed_data_3)
    assert parsed_data_3["type"] == "unparsed_access_log"

    print("\n--- Test Log Line 4 ---")
    parsed_data_4, _ = parser.parse(log_line_4, source="apache_access")
    print(parsed_data_4)
    assert parsed_data_4["path"] == "/admin/update"
    assert parsed_data_4["method"] == "PUT"

    print("\nAll AccessLogParser tests passed!")
