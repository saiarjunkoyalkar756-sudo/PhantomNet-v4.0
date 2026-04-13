# backend_api/siem_integration_service/log_normalizer.py

import asyncio
import logging
import json
import re
from typing import Dict, Any, Optional
from typing import Dict, Any, Optional
from datetime import datetime
import uuid # Import uuid

from shared.logger_config import logger
from .schemas import RawLog, NormalizedLog # Import models

logger = logger

class LogNormalizer:
    """
    Normalizes raw log events into a structured, common schema (NormalizedLog).
    This class would contain various parsers for different log formats.
    """
    def __init__(self):
        logger.info("LogNormalizer initialized.")
        # Load parsing rules/regexes/templates from configuration or a database
        # self.parsing_rules = self._load_parsing_rules()

    async def _parse_json_log(self, raw_data: str, source_system: str, host: Optional[str]) -> Optional[NormalizedLog]:
        """Parses a raw JSON log."""
        try:
            data = json.loads(raw_data)
            
            # Example mapping for a generic JSON log
            event_type = data.get("event_type", "generic.json_event")
            message = data.get("message", "JSON event received")
            timestamp_str = data.get("timestamp") or data.get("time")
            
            timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()

            return NormalizedLog(
                event_id=str(uuid.uuid4()), # Assuming uuid is imported
                timestamp=timestamp,
                event_type=event_type,
                source_system=source_system,
                host_id=host,
                message=message,
                full_data=data,
            )
        except json.JSONDecodeError:
            logger.warning("Raw data is not valid JSON.")
            return None
        except Exception as e:
            logger.error(f"Error parsing JSON log: {e}", exc_info=True)
            return None

    async def _parse_syslog_cef_log(self, raw_data: str, source_system: str, host: Optional[str]) -> Optional[NormalizedLog]:
        """
        Parses a raw syslog/CEF formatted log.
        Simplified for demonstration; full CEF parsing is complex.
        """
        cef_pattern = re.compile(r"CEF:\d+\|(?P<vendor>[^|]+)\|(?P<product>[^|]+)\|(?P<version>[^|]+)\|(?P<event_id>[^|]+)\|(?P<name>[^|]+)\|(?P<severity>[^|]+)\|(.*)")
        match = cef_pattern.match(raw_data)
        
        if match:
            groups = match.groupdict()
            message = f"{groups['name']} ({groups['event_id']})"
            full_data = {"cef_vendor": groups["vendor"], "cef_product": groups["product"], **groups} # Store all CEF parts

            return NormalizedLog(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                event_type=f"cef.{groups['event_id']}",
                severity=groups["severity"].lower(),
                source_system=source_system,
                host_id=host,
                message=message,
                full_data=full_data,
            )
        else:
            # Fallback for generic syslog if not CEF
            syslog_pattern = re.compile(r"(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+([\w\d\.-]+)\s+(.*)")
            match = syslog_pattern.match(raw_data)
            if match:
                # Need to handle year for syslog dates
                log_time_str = match.group(1) # e.g., Jan  1 00:00:00
                log_host = match.group(2)
                log_message = match.group(3)
                
                # Assume current year for simplicity
                timestamp = datetime.strptime(f"{datetime.now().year} {log_time_str}", "%Y %b %d %H:%M:%S")
                
                return NormalizedLog(
                    event_id=str(uuid.uuid4()),
                    timestamp=timestamp,
                    event_type="syslog.generic",
                    source_system=source_system,
                    host_id=log_host,
                    message=log_message,
                    full_data={"raw_syslog_message": raw_data},
                )
            logger.warning(f"Unsupported log format: {raw_data[:100]}...")
            return None

    async def normalize_log(self, raw_log: RawLog) -> Optional[NormalizedLog]:
        """
        Normalizes a raw log entry based on its content and source system.
        """
        logger.debug(f"Normalizing log from {raw_log.source_system}. Raw data preview: {raw_log.raw_data[:50]}...")
        
        # Try JSON first
        normalized = await self._parse_json_log(raw_log.raw_data, raw_log.source_system, raw_log.host)
        if normalized:
            normalized.raw_log_id = str(uuid.uuid4()) # Link back to raw log if stored
            return normalized

        # Try CEF/Syslog
        normalized = await self._parse_syslog_cef_log(raw_log.raw_data, raw_log.source_system, raw_log.host)
        if normalized:
            normalized.raw_log_id = str(uuid.uuid4())
            return normalized

        # Fallback for unparseable logs
        logger.warning(f"Could not normalize log from {raw_log.source_system}. Storing as generic event.")
        return NormalizedLog(
            event_id=str(uuid.uuid4()),
            timestamp=raw_log.timestamp,
            event_type="generic.unparsed_log",
            severity="info",
            source_system=raw_log.source_system,
            host_id=raw_log.host,
            message="Unparsed log event",
            full_data={"raw_data": raw_log.raw_data},
            raw_log_id=str(uuid.uuid4())
        )

# Example usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running LogNormalizer example...")
    
    # Needs uuid import
    import uuid

    async def run_example():
        normalizer = LogNormalizer()

        # Test JSON log
        raw_log_json = RawLog(
            source_system="agent-linux-001",
            host="linux-server",
            raw_data='{"event_type": "process.create", "process_name": "bash", "user": "root", "pid": 1234, "timestamp": "2023-10-27T10:00:00Z", "message": "New process created"}'
        )
        normalized_json = await normalizer.normalize_log(raw_log_json)
        logger.info(f"\nNormalized JSON Log:\n{normalized_json.model_dump_json(indent=2)}")

        # Test CEF log
        raw_log_cef = RawLog(
            source_system="firewall-001",
            host="firewall.corp",
            raw_data='<187>Jan 1 00:00:00 firewall CEF:0|PaloAltoNetworks|PAN-OS|9.1.0|threat|THREAT_ வைரस|1|dvc=192.168.1.1 suser=admin duser=jdoe fname=eicar.txt act=blocked'
        )
        normalized_cef = await normalizer.normalize_log(raw_log_cef)
        logger.info(f"\nNormalized CEF Log:\n{normalized_cef.model_dump_json(indent=2)}")
        
        # Test generic syslog
        raw_log_syslog = RawLog(
            source_system="router-001",
            host="router.corp",
            raw_data='Jan 1 12:00:00 router.corp %SEC-6-IPACCESSLOGP: list 102 denied tcp 192.168.2.1(1234) -> 10.0.0.1(80), 1 packet'
        )
        normalized_syslog = await normalizer.normalize_log(raw_log_syslog)
        logger.info(f"\nNormalized SYSLOG Log:\n{normalized_syslog.model_dump_json(indent=2)}")

        # Test unparseable log
        raw_log_unparseable = RawLog(
            source_system="unknown",
            host="bad-host",
            raw_data='This is some random unparseable text data'
        )
        normalized_unparseable = await normalizer.normalize_log(raw_log_unparseable)
        logger.info(f"\nNormalized Unparseable Log:\n{normalized_unparseable.model_dump_json(indent=2)}")


    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("LogNormalizer example stopped.")
