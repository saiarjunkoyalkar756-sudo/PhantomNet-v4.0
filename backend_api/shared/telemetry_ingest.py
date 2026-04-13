import asyncio
import time
import uuid
import json
import os
import importlib
import inspect # Added for dynamic module inspection
from typing import Dict, Any, Union, Tuple, Optional, List
from pydantic import BaseModel, Field, ValidationError
from loguru import logger
import concurrent.futures

from backend_api.log_parsers.base_parser import BaseLogParser
from .schemas import RawEvent
from .cassandra_client import CassandraClient # Import CassandraClient
from backend_api.core_config import SAFE_MODE

# Conditional import for Kafka
if not SAFE_MODE:
    from kafka import KafkaProducer
else:
    # Define a dummy KafkaProducer if SAFE_MODE is enabled
    class KafkaProducer:
        def __init__(self, *args, **kwargs):
            logger.warning("SAFE_MODE: KafkaProducer is a dummy object.")
        def send(self, *args, **kwargs):
            pass
        def flush(self):
            pass

class TelemetryIngestConfig(BaseModel):
    """Configuration parameters for the TelemetryIngestService."""
    kafka_bootstrap_servers: str = "localhost:9092"
    raw_telemetry_topic: str = "phantomnet.raw_telemetry"
    parser_plugins_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log_parsers")
    
    # Cassandra (Telemetry Data DB) Configuration
    cassandra_contact_points: List[str] = ["localhost"]
    cassandra_keyspace: str = "phantomnet_telemetry"


class TelemetryIngestService:
    def __init__(self, raw_event_queue: asyncio.Queue, config: TelemetryIngestConfig = TelemetryIngestConfig()):
        self.raw_event_queue = raw_event_queue # Still maintain internal queue for immediate processing feedback or if Kafka is down
        self.config = config
        self.parsers: Dict[str, BaseLogParser] = {}
        self._load_parsers()
        try:
            self.kafka_producer = KafkaProducer(bootstrap_servers=self.config.kafka_bootstrap_servers.split(','))
        except Exception as e:
            logger.warning(f"Could not connect to Kafka, telemetry will not be published: {e}")
            self.kafka_producer = None
        
        if not SAFE_MODE and self.kafka_producer:
            self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1) # KafkaProducer is synchronous
        else:
            self.executor = None # No need for executor if Kafka is disabled
        self.cassandra_client = CassandraClient(
            contact_points=self.config.cassandra_contact_points,
            keyspace=self.config.cassandra_keyspace
        )

    def _load_parsers(self):
        """
        Dynamically loads log parsers from the specified parser_plugins_path.
        Parsers must inherit from BaseLogParser.
        """
        parser_dir = self.config.parser_plugins_path
        logger.info(f"Loading parsers from: {parser_dir}")
        for filename in os.listdir(parser_dir):
            if filename.endswith(".py") and not filename.startswith(
                ("__init__", "base_parser")
            ):
                module_name = filename[:-3]  # Remove .py extension
                try:
                    # Dynamically import the module
                    # We need to construct the full import path, assuming it's relative to backend_api
                    full_module_path = f"backend_api.log_parsers.{module_name}"
                    module = importlib.import_module(full_module_path)

                    # Inspect the module for classes that inherit from BaseLogParser
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, BaseLogParser)
                            and obj is not BaseLogParser
                        ):
                            parser_instance = obj()
                            self.parsers[parser_instance.name] = parser_instance
                            logger.info(f"Loaded parser: {parser_instance.name}")
                            break # Assume one parser class per file
                except Exception as e:
                    logger.error(f"Error loading parser from {filename}: {e}")

    async def ingest_raw_log(self, log_entry: Union[str, Dict[str, Any]], source: str, agent_id: Optional[str] = None, agent_os: Optional[str] = None, agent_capabilities: Optional[Dict[str, Any]] = None):
        """
        Ingests a raw log entry and attempts to parse it into a RawEvent.
        Publishes the RawEvent to Kafka and also puts it into the internal queue.
        """
        parsed_data, raw_log_str = self._parse_log_entry(log_entry, source)

        try:
            event_type = parsed_data.get("type", "unknown_log")
            if not event_type and isinstance(log_entry, str):
                if "syslog" in log_entry.lower():
                    event_type = "syslog"
                elif "apache" in log_entry.lower() or "nginx" in log_entry.lower():
                    event_type = "web_access_log"
            elif (
                not event_type
                and isinstance(log_entry, dict)
                and "event_type" in log_entry
            ):
                event_type = log_entry["event_type"]

            event = RawEvent(
                source=source,
                type=event_type,
                agent_id=agent_id,
                agent_os=agent_os,
                agent_capabilities=agent_capabilities,
                data=parsed_data,
                raw_log=raw_log_str
            )
            logger.info(
                f"[TelemetryIngest] Ingesting raw log from {source} (type: {event_type}) from agent {agent_id} ({agent_os})"
            )
            
            # Publish to Kafka if available
            if not SAFE_MODE:
                event_bytes = event.model_dump_json().encode('utf-8')
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self.executor, self.kafka_producer.send, self.config.raw_telemetry_topic, event_bytes)
                self.kafka_producer.flush() # Ensure message is sent
                logger.debug(f"[TelemetryIngest] Sent RawEvent {event.id} to Kafka topic {self.config.raw_telemetry_topic}")
            else:
                logger.warning(f"SAFE_MODE is ON. Skipping Kafka publish for RawEvent {event.id}.")

            # Persist to Cassandra
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, self.cassandra_client.save_raw_event, event)
            logger.debug(f"[TelemetryIngest] Saved RawEvent {event.id} to Cassandra.")

            # Also put into internal queue (for immediate processing or fallback)
            await self.raw_event_queue.put(event)

        except ValidationError as e:
            logger.error(
                f"Failed to validate raw log from {source} as RawEvent: {e}. Original: {raw_log_str[:200]}..."
            )
        except Exception as e:
            logger.error(
                f"Error ingesting raw log from {source}: {e}. Original: {raw_log_str[:200]}..."
            )

    def _parse_log_entry(
        self, log_entry: Union[str, Dict[str, Any]], source: str
    ) -> Tuple[Dict[str, Any], str]:
        """
        Attempts to parse a raw log entry using registered parsers.
        Prioritizes parsers based on 'source' hint, then tries general JSON/plaintext.
        Returns (parsed_data_dict, original_raw_log_string)
        """
        raw_log_str = ""
        parsed_data: Dict[str, Any] = {}

        if isinstance(log_entry, dict):
            parsed_data = log_entry
            raw_log_str = json.dumps(log_entry)
        elif isinstance(log_entry, str):
            raw_log_str = log_entry

            # Try to use a parser based on the 'source' hint
            for parser_name, parser in self.parsers.items():
                if source.lower() in parser.supported_types or any(
                    t in source.lower() for t in parser.supported_types
                ):
                    try:
                        logger.debug(
                            f"Attempting to parse with {parser.name} based on source '{source}'"
                        )
                        parsed_data, raw_log_str = parser.parse(raw_log_str, source)
                        if parsed_data and (
                            len(parsed_data) > 1
                            or (len(parsed_data) == 1 and "message" not in parsed_data)
                        ):
                            return parsed_data, raw_log_str
                    except Exception as e:
                        logger.warning(
                            f"Parser {parser.name} failed for source {source}: {e}"
                        )

            # Fallback: Try JSON parser explicitly if no source-specific parser worked well
            if "json_parser" in self.parsers:
                try:
                    logger.debug("Attempting fallback JSON parsing.")
                    parsed_data, raw_log_str = self.parsers["json_parser"].parse(
                        raw_log_str, source
                    )
                    if parsed_data and (
                        len(parsed_data) > 1
                        or (len(parsed_data) == 1 and "message" not in parsed_data)
                    ):
                        return parsed_data, raw_log_str
                except Exception as e:
                    logger.warning(f"Fallback JSON parser failed: {e}")

            # Final fallback: Treat as plain text
            parsed_data = {"message": log_entry}
        else:
            parsed_data = {"message": str(log_entry)}
            raw_log_str = str(log_entry)

        return parsed_data, raw_log_str