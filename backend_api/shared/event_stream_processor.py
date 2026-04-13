# backend_api/event_stream_processor.py
import asyncio
import time
import random
import uuid  # Added for UUID generation
import json  # Added for JSON parsing
import collections # Import collections module
from typing import Dict, Any, List, Optional, Union, Tuple
from pydantic import BaseModel, Field, ValidationError
from loguru import logger  # Import loguru logger
import concurrent.futures

from . import database, schemas
from .schemas import RawEvent, CorrelatedEvent
from .telemetry_ingest import TelemetryIngestService, TelemetryIngestConfig
from .cassandra_client import CassandraClient # Import CassandraClient
from backend_api.core_config import SAFE_MODE

# Conditional import for Kafka
if not SAFE_MODE:
    from kafka import KafkaConsumer, KafkaProducer
else:
    # Define dummy classes if SAFE_MODE is enabled to prevent ModuleNotFoundError
    class KafkaConsumer:
        def __init__(self, *args, **kwargs):
            logger.warning("SAFE_MODE: KafkaConsumer is a dummy object.")
        def poll(self, *args, **kwargs):
            return None
        def close(self):
            pass

    class KafkaProducer:
        def __init__(self, *args, **kwargs):
            logger.warning("SAFE_MODE: KafkaProducer is a dummy object.")
        def send(self, *args, **kwargs):
            pass
        def flush(self):
            pass

class EventStreamProcessor:
    def __init__(self, websocket_broadcaster, plugin_manager, db_session_generator, telemetry_ingest_service, kafka_bootstrap_servers, raw_telemetry_topic, cassandra_contact_points, cassandra_keyspace, alert_db_host=None, alert_db_port=None, **kwargs):
        self.websocket_broadcaster = websocket_broadcaster
        self.plugin_manager = plugin_manager
        self.db_session_generator = db_session_generator
        self.telemetry_ingest_service = telemetry_ingest_service
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.raw_telemetry_topic = raw_telemetry_topic
        self.alert_db_host = alert_db_host
        self.alert_db_port = alert_db_port
        
        self.raw_event_queue = asyncio.Queue()
        self.correlated_event_queue = asyncio.Queue()
        self.event_history = collections.deque(maxlen=10000)
        self.user_baselines = {}
        self.host_baselines = {}
        self.threat_intel_iocs = []

        try:
            self.kafka_consumer = KafkaConsumer(
                self.raw_telemetry_topic,
                bootstrap_servers=self.kafka_bootstrap_servers,
                auto_offset_reset='earliest',
                group_id='phantomnet_event_stream_processor'
            )
        except Exception as e:
            logger.warning(f"Could not connect to Kafka, event stream processor will not consume events: {e}")
            self.kafka_consumer = None
        
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap_servers
            )
        except Exception as e:
            logger.warning(f"Could not connect to Kafka, event stream processor will not be able to produce events: {e}")
            self.kafka_producer = None
        
        if not SAFE_MODE and self.kafka_producer:
            self.producer_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1) # For synchronous KafkaProducer
        else:
            self.producer_executor = None

        # Initialize database clients
        self.cassandra_client = CassandraClient(cassandra_contact_points, cassandra_keyspace)

        self.ai_correlation_plugin_name = "Anomaly Detector AI"
        if self.plugin_manager.available_plugins.get(self.ai_correlation_plugin_name):
            self.loaded_ai_correlation = self.plugin_manager.load_plugin(
                self.ai_correlation_plugin_name
            )
        else:
            self.loaded_ai_correlation = False


    def _normalize_event(self, raw_event: RawEvent) -> schemas.NormalizedEvent:
        """
        Normalizes a RawEvent into a standardized NormalizedEvent schema (ECS/CIM-like).
        This is a placeholder for more complex normalization logic.
        """
        normalized_data = {
            "event_id": raw_event.id,
            "timestamp": raw_event.timestamp,
            "source": raw_event.source,
            "event_type": raw_event.type,
            "raw_data": (
                raw_event.raw_log if raw_event.raw_log else json.dumps(raw_event.data)
            ),
            "metadata": raw_event.data,  # Store original parsed data as metadata
        }

        # Define a flexible mapping for common fields
        field_mappings = {
            "host_name": ["host", "hostname", "device_name"],
            "user_name": ["user", "username", "account_name"],
            "src_ip": ["ip", "src_ip", "source_ip_address"],
            "dest_ip": ["dest_ip", "destination_ip_address"],
            "src_port": ["src_port", "source_port"],
            "dest_port": ["dest_port", "destination_port"],
            "process_name": ["process", "process_name"],
            "file_path": ["file", "filepath", "path"],
        }

        # Dynamically extract fields based on mappings
        for normalized_field, possible_raw_keys in field_mappings.items():
            for key in possible_raw_keys:
                if key in raw_event.data and raw_event.data[key] is not None:
                    normalized_data[normalized_field] = raw_event.data[key]
                    break # Take the first match

        try:
            return schemas.NormalizedEvent(**normalized_data)
        except ValidationError as e:
            logger.error(
                f"Error normalizing event {raw_event.id}: {e}. Data: {normalized_data}"
            )
            # Fallback to a minimal NormalizedEvent if validation fails
            return schemas.NormalizedEvent(
                event_id=raw_event.id,
                timestamp=raw_event.timestamp,
                source=raw_event.source,
                event_type=raw_event.type,
                raw_data=(
                    raw_event.raw_log
                    if raw_event.raw_log
                    else json.dumps(raw_event.data)
                ),
                metadata={},
            )

    async def _consume_raw_events_from_kafka(self):
        """
        Consumes raw telemetry messages from Kafka, validates them,
        and puts them into the internal raw_event_queue.
        """
        if SAFE_MODE:
            logger.warning("SAFE_MODE is ON. Kafka consumer for raw events is disabled.")
            return # Exit if kafka is not available

        loop = asyncio.get_running_loop()
        while True:
            messages = await loop.run_in_executor(None, self.kafka_consumer.poll, 1000) # Poll for 1 second
            if messages is None:
                continue
            for topic_partition, message_list in messages.items():
                for message in message_list:
                    try:
                        if message.value is None:
                            logger.warning("Received None message value from Kafka.")
                            continue

                        message_str = message.value.decode('utf-8')
                        raw_event_dict = json.loads(message_str)
                        raw_event = schemas.RawEvent(**raw_event_dict)
                        await self.raw_event_queue.put(raw_event)
                        logger.debug(f"[EventStream] Consumed RawEvent {raw_event.id} from Kafka and queued for processing.")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode Kafka message as JSON: {e}. Message: {message_str[:200]}...")
                    except ValidationError as e:
                        logger.error(f"Failed to validate Kafka message as RawEvent: {e}. Message: {message_str[:200]}...")
                    except Exception as e:
                        logger.error(f"Unexpected error consuming from Kafka: {e}")
            await asyncio.sleep(0.1) # Small delay to prevent busy-waiting


    async def _save_normalized_event(self, normalized_event: schemas.NormalizedEvent):
        """Persists a normalized event to the database using the Cassandra client."""
        await self.cassandra_client.save_normalized_event(normalized_event)
        logger.debug(
            f"Saved normalized event {normalized_event.event_id} to Cassandra."
        )

    async def _save_correlated_event(self, correlated_event: schemas.CorrelatedEvent):
        """
        Publishes a correlated event (alert) to Kafka for the Alert Manager to persist and process.
        """
        logger.info(f"Publishing CorrelatedEvent {correlated_event.id} to Kafka for Alert Manager.")
        # In a real system, this would publish to a Kafka topic for the Alert Manager (e.g., "phantomnet.alerts")
        # For now, we simulate this by just logging.
        # await self.alert_kafka_producer.send("phantomnet.alerts", correlated_event.model_dump_json().encode('utf-8'))
        # await self.alert_kafka_producer.flush()

    async def _enrich_normalized_event(self, normalized_event: schemas.NormalizedEvent) -> schemas.NormalizedEvent:
        """
        Simulates enriching a NormalizedEvent with external data (e.g., asset inventory, CMDB, identity).
        In a real scenario, this would involve async calls to dedicated microservices or databases.
        """
        logger.debug(f"Attempting to enrich event {normalized_event.event_id}")

        # Simulate asset inventory lookup
        if normalized_event.host_name:
            # Example: look up host details from a mock asset inventory
            mock_asset_data = {
                "server_1": {"owner": "IT_Dept", "location": "DC1", "criticality": "high"},
                "web_server_01": {"owner": "Web_Team", "location": "AWS_Region_X", "criticality": "medium"},
            }
            if normalized_event.host_name.lower() in mock_asset_data:
                normalized_event.metadata["asset_info"] = mock_asset_data[normalized_event.host_name.lower()]
                logger.debug(f"Enriched event {normalized_event.event_id} with asset info for {normalized_event.host_name}")

        # Simulate user identity lookup
        if normalized_event.user_name:
            # Example: look up user roles from a mock identity provider
            mock_user_data = {
                "admin": {"roles": ["admin", "security_ops"], "department": "Security"},
                "analyst": {"roles": ["security_analyst"], "department": "SOC"},
            }
            if normalized_event.user_name.lower() in mock_user_data:
                normalized_event.metadata["user_info"] = mock_user_data[normalized_event.user_name.lower()]
                logger.debug(f"Enriched event {normalized_event.event_id} with user info for {normalized_event.user_name}")
        
        # Simulate geo-IP enrichment
        if normalized_event.src_ip:
            # Simple mock geo-IP
            if normalized_event.src_ip.startswith("192.") or normalized_event.src_ip.startswith("10."):
                normalized_event.metadata["geo_ip"] = {"country": "Internal", "city": "N/A"}
            else:
                normalized_event.metadata["geo_ip"] = {"country": "External", "city": "Unknown"}
            logger.debug(f"Enriched event {normalized_event.event_id} with geo-IP for {normalized_event.src_ip}")


        return normalized_event

    async def _process_raw_events(self):
        """
        Processes raw events, normalizing them, enriching them, saving to DB, and pushing for correlation.
        """
        while True:
            event = await self.raw_event_queue.get()
            logger.debug(
                f"[EventStream] Processing raw event {event.id} for normalization, enrichment and persistence."
            )

            # 1. Normalize the event
            normalized_event = self._normalize_event(event)

            # 2. Enrich the normalized event
            enriched_event = await self._enrich_normalized_event(normalized_event)

            # 3. Save the normalized (and now enriched) event to the database
            try:
                await self._save_normalized_event(enriched_event)
            except Exception as e:
                logger.error(
                    f"Failed to save normalized event {enriched_event.event_id} to DB: {e}"
                )

            # 4. Publish processed telemetry to Kafka
            if not SAFE_MODE and self.kafka_producer:
                processed_event_bytes = enriched_event.model_dump_json().encode('utf-8')
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self.producer_executor, self.kafka_producer.send, "phantomnet.processed_telemetry", processed_event_bytes)
                self.kafka_producer.flush() # Ensure message is sent
                logger.debug(f"[EventStream] Published ProcessedEvent {enriched_event.event_id} to Kafka topic phantomnet.processed_telemetry")

            # 5. Push the original RawEvent for correlation (or normalized_event if correlation expects it)
            # For now, correlation expects RawEvent, so we push the original.
            await self.correlated_event_queue.put(event)
            self.raw_event_queue.task_done()

    def _evaluate_correlation_rules(self, current_event: RawEvent) -> Optional[Dict[str, Any]]:
        """
        Evaluates predefined rules against the current event and historical events
        to identify multi-stage attack patterns.
        """
        # Rule 1: Network scan followed by login attempt failure from same source
        if current_event.type == "login_attempt_failure":
            source_ip = current_event.data.get("src_ip")
            if source_ip:
                for past_event in reversed(self.event_history): # Search recent history
                    # Check for network scan from the same IP within a time window (e.g., 5 minutes)
                    if (past_event.type == "network_scan" or past_event.type == "port_scan") and \
                       past_event.data.get("src_ip") == source_ip and \
                       (current_event.timestamp - past_event.timestamp) < 300: # 5 minutes
                        
                        logger.warning(
                            f"Rule triggered: Brute Force Attempt from {source_ip} "
                            f"(Scan: {past_event.id}, Login Failure: {current_event.id})"
                        )
                        return {
                            "is_correlated": True,
                            "correlation_type": "brute_force_attempt",
                            "severity": "high",
                            "description": f"Network scan from {source_ip} followed by login attempt failure.",
                            "related_events": [past_event.id, current_event.id]
                        }
        
        # Rule 2: Slow Data Exfiltration (temporal correlation over a longer period)
        # Looking for multiple small outbound data transfers to an external IP from the same host
        if current_event.type == "data_transfer" and current_event.data.get("direction") == "outbound":
            dest_ip = current_event.data.get("dest_ip")
            src_host = current_event.data.get("host_name")
            data_size = current_event.data.get("size", 0)

            # Check if destination IP is external (simplified check) and data size is small
            if dest_ip and not (dest_ip.startswith("192.168.") or dest_ip.startswith("10.") or dest_ip.startswith("172.16.")) and data_size < 1024 * 1024: # Less than 1MB
                exfiltration_events = [current_event.id]
                transfer_count = 1
                total_data_transferred = data_size
                time_window = 3600 # 1 hour window for slow exfiltration

                for past_event in reversed(self.event_history):
                    if past_event.type == "data_transfer" and \
                       past_event.data.get("direction") == "outbound" and \
                       past_event.data.get("dest_ip") == dest_ip and \
                       past_event.data.get("host_name") == src_host and \
                       (current_event.timestamp - past_event.timestamp) < time_window and \
                       past_event.data.get("size", 0) < 1024 * 1024:
                        
                        transfer_count += 1
                        total_data_transferred += past_event.data.get("size", 0)
                        exfiltration_events.append(past_event.id)
                
                # If multiple small transfers detected
                if transfer_count >= 5 and total_data_transferred > (1024 * 1024 * 2): # At least 5 small transfers, totaling over 2MB
                    logger.critical(
                        f"Rule triggered: Potential Slow Data Exfiltration from {src_host} to {dest_ip} "
                        f"({transfer_count} small transfers, {total_data_transferred / (1024*1024):.2f} MB over {time_window/60} mins)"
                    )
                    return {
                        "is_correlated": True,
                        "correlation_type": "slow_data_exfiltration",
                        "severity": "critical",
                        "description": f"Multiple small outbound data transfers from {src_host} to {dest_ip}.",
                        "related_events": exfiltration_events
                    }

        # Add more correlation rules here as needed
        # Rule 3: Multiple failed login attempts from different users on the same host
        # Rule 4: Anomalous outbound connection after successful login

        return None

    async def _correlate_events_with_ai(self):
        """Correlates events using an AI plugin or simulation, and rule-based correlation."""
        while True:
            event_to_correlate = await self.correlated_event_queue.get()
            logger.debug(
                f"[EventStream] Correlating event {event_to_correlate.id} with AI and rules"
            )

            # Add event to history for rule-based correlation
            self.event_history.append(event_to_correlate)

            # 1. Rule-based correlation
            correlation_findings = self._evaluate_correlation_rules(event_to_correlate)

            if correlation_findings and correlation_findings.get("is_correlated"):
                # If rule-based correlation finds something, prioritize it
                correlated_event = CorrelatedEvent(
                    id=event_to_correlate.id,
                    timestamp=event_to_correlate.timestamp,
                    source=event_to_correlate.source,
                    type=correlation_findings["correlation_type"],
                    data=event_to_correlate.data,
                    correlation_id=str(uuid.uuid4()),
                    related_events=correlation_findings.get("related_events", []),
                    severity=correlation_findings["severity"],
                    ai_score=1.0, # Assign high confidence for rule-triggered events
                    action_recommendation=correlation_findings.get("description"),
                )
                logger.critical(
                    f"[EventStream] RULE-BASED ALERT (Severity: {correlated_event.severity}, Type: {correlated_event.type}) for event {correlated_event.id}"
                )
                await self.websocket_broadcaster(
                    {"type": "correlated_alert", "alert": correlated_event.dict()}
                )
                await self._save_correlated_event(correlated_event) # Save to alert DB
            else:
                # 2. Threat Intelligence lookup
                ti_match = self._check_threat_intelligence(event_to_correlate)
                if ti_match:
                    correlated_event = CorrelatedEvent(
                        id=event_to_correlate.id,
                        timestamp=event_to_correlate.timestamp,
                        source=event_to_correlate.source,
                        type="threat_intelligence_match",
                        data=event_to_correlate.data,
                        correlation_id=str(uuid.uuid4()),
                        related_events=[event_to_correlate.id],
                        severity="critical",
                        ai_score=1.0, # Highest confidence for TI matches
                        action_recommendation=f"Threat Intelligence Match: {ti_match['description']}",
                    )
                    logger.critical(
                        f"[EventStream] THREAT INTEL ALERT (Severity: critical, Type: {correlated_event.type}) for event {correlated_event.id}"
                    )
                    await self.websocket_broadcaster(
                        {"type": "correlated_alert", "alert": correlated_event.dict()}
                    )
                    await self._save_correlated_event(correlated_event) # Save to alert DB
                else:
                    # 3. AI-based correlation (if no rule or TI match was triggered)
                    correlated_event_data = await self._run_ai_correlation(event_to_correlate)

                    # Simulate real-time alerts with priority scoring
                    if (
                        correlated_event_data.get("is_anomaly", False)
                        or correlated_event_data.get("ai_score", 0) > 0.7
                    ):
                        severity_map = {0.0: "low", 0.5: "medium", 0.7: "high", 0.9: "critical"}
                        current_severity = next(
                            (
                                s
                                for score, s in sorted(severity_map.items())
                                if correlated_event_data.get("ai_score", 0) >= score
                            ),
                            "low",
                        )

                        correlated_event = CorrelatedEvent(
                            id=event_to_correlate.id,
                            timestamp=event_to_correlate.timestamp,
                            source=event_to_correlate.source,
                            type=event_to_correlate.type,
                            data=event_to_correlate.data,
                            correlation_id=str(uuid.uuid4()),
                            related_events=[event_to_correlate.id],
                            severity=current_severity,
                            ai_score=correlated_event_data.get("ai_score", 0.0),
                            action_recommendation=correlated_event_data.get("suggested_action"),
                        )
                        logger.warning(
                            f"[EventStream] Real-time Alert (Severity: {correlated_event.severity}, Score: {correlated_event.ai_score:.2f}) for event {correlated_event.id}"
                        )
                        await self.websocket_broadcaster(
                            {"type": "correlated_alert", "alert": correlated_event.dict()}
                        )
                        await self._save_correlated_event(correlated_event) # Save to alert DB
                    else:
                        logger.info(
                            f"[EventStream] Event {event_to_correlate.id} processed, no high correlation detected."
                        )
                        # Still broadcast to dashboards for live updates if not an alert
                        await self.websocket_broadcaster(
                            {"type": "processed_event", "event": event_to_correlate.dict()}
                        )

            self.correlated_event_queue.task_done()

    async def _enrich_alert(self, correlated_event: CorrelatedEvent) -> CorrelatedEvent:
        """
        Conceptual method to enrich a CorrelatedEvent (alert) with additional context
        before persistence and notification.
        E.g., add incident ID, suggested playbooks, links to asset inventory, etc.
        """
        logger.debug(f"Conceptually enriching alert {correlated_event.id}")
        # Simulate adding an incident ID
        if "incident_id" not in correlated_event.data:
            correlated_event.data["incident_id"] = str(uuid.uuid4())
        
        # Simulate adding playbook suggestions based on alert type/severity
        if correlated_event.type == "brute_force_attempt" and correlated_event.severity == "high":
            correlated_event.data["suggested_playbooks"] = ["BruteForceResponsePlaybook"]
        
        return correlated_event

    def _check_threat_intelligence(self, event: RawEvent) -> Optional[Dict[str, str]]:
        """
        Checks the event data against known threat intelligence IOCs.
        """
        # Extract potential IOCs from the event data
        potential_iocs = []
        if event.data.get("src_ip"):
            potential_iocs.append({"type": "ip", "value": event.data["src_ip"]})
        if event.data.get("dest_ip"):
            potential_iocs.append({"type": "ip", "value": event.data["dest_ip"]})
        if event.data.get("domain"):
            potential_iocs.append({"type": "domain", "value": event.data["domain"]})
        if event.data.get("file_hash"):
            potential_iocs.append({"type": "hash", "value": event.data["file_hash"]})
        
        # Check against loaded threat intelligence
        for ioc in self.threat_intel_iocs:
            for potential_ioc in potential_iocs:
                if ioc["type"] == potential_ioc["type"] and ioc["value"] == potential_ioc["value"]:
                    logger.critical(f"Threat Intelligence Match: {ioc['description']} for {ioc['type']}:{ioc['value']}")
                    return ioc # Return the matching IOC
        return None

    async def _run_ai_correlation(self, event_data: RawEvent) -> Dict[str, Any]:
        """Runs the AI correlation plugin or simulates its output, including basic UEBA."""
        # Initialize UEBA-related flags
        is_ueba_anomaly = False
        ueba_score = 0.0
        ueba_reason = ""

        # Extract relevant entities for UEBA
        normalized_event = self._normalize_event(event_data) # Use normalization for entities
        user_name = normalized_event.user_name
        host_name = normalized_event.host_name
        event_type = normalized_event.event_type

        # --- Simulate UEBA: Develop baseline models and detect deviations ---
        if user_name:
            if user_name not in self.user_baselines:
                self.user_baselines[user_name] = {"activity_counts": collections.defaultdict(int), "last_activity": time.time()}
                logger.info(f"Establishing new baseline for user: {user_name}")
            
            user_baseline = self.user_baselines[user_name]
            user_baseline["activity_counts"][event_type] += 1
            user_baseline["last_activity"] = time.time()

            # Simple deviation detection: unusual activity type for user
            if user_baseline["activity_counts"][event_type] < 3 and user_baseline["activity_counts"].get("total", 0) > 10:
                is_ueba_anomaly = True
                ueba_score = max(ueba_score, 0.6) # Moderate anomaly
                ueba_reason = f"Unusual activity type '{event_type}' for user '{user_name}'."
                logger.warning(f"[UEBA] {ueba_reason}")

        if host_name:
            if host_name not in self.host_baselines:
                self.host_baselines[host_name] = {"activity_counts": collections.defaultdict(int), "last_activity": time.time()}
                logger.info(f"Establishing new baseline for host: {host_name}")
            
            host_baseline = self.host_baselines[host_name]
            host_baseline["activity_counts"][event_type] += 1
            host_baseline["last_activity"] = time.time()

            # Simple deviation detection: unusual activity type for host
            if host_baseline["activity_counts"][event_type] < 3 and host_baseline["activity_counts"].get("total", 0) > 10:
                is_ueba_anomaly = True
                ueba_score = max(ueba_score, 0.7) # Higher anomaly
                ueba_reason = f"Unusual activity type '{event_type}' for host '{host_name}'."
                logger.warning(f"[UEBA] {ueba_reason}")
        
        # Update total activity counts (simplified)
        if user_name: self.user_baselines[user_name]["activity_counts"]["total"] += 1
        if host_name: self.host_baselines[host_name]["activity_counts"]["total"] += 1


        # --- AI Plugin or Fallback Simulation ---
        plugin_anomaly_result = None
        if self.loaded_ai_correlation:
            try:
                result = self.plugin_manager.execute_plugin_function(
                    self.ai_correlation_plugin_name,
                    "analyze_event_for_anomaly",
                    event_data.dict(),
                )
                if result and not result.get("error"):
                    plugin_anomaly_result = result
                else:
                    logger.error(
                        f"Error calling AI correlation plugin: {result.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                logger.error(f"Exception during AI correlation plugin call: {e}")

        # Combine results from UEBA and AI plugin/simulation
        ai_score = 0.0
        is_anomaly = False
        suggested_action = "Monitor"
        detection_type = "none" # Default detection type

        if plugin_anomaly_result:
            is_anomaly = plugin_anomaly_result.get("is_anomaly", False)
            ai_score = plugin_anomaly_result.get("anomaly_score", 0.0)
            suggested_action = plugin_anomaly_result.get("suggested_action", "Investigate")
            detection_type = plugin_anomaly_result.get("detection_type", "anomaly") # e.g., "anomaly", "signature"
        else:
            # Fallback to simple AI simulation if plugin is not loaded or fails
            ai_score_sim = random.uniform(0.0, 0.4)
            if random.random() < 0.1: # 10% chance of random AI anomaly
                ai_score_sim = random.uniform(0.7, 1.0)
                is_anomaly = True
                suggested_action = "Simulated AI Investigate"
                detection_type = random.choice(["anomaly", "signature"]) # Randomly assign for simulation
            
            ai_score = max(ai_score, ai_score_sim) # Take the max score
            is_anomaly = is_anomaly or (ai_score > 0.7)


        # Prioritize UEBA findings if they indicate a stronger anomaly
        if is_ueba_anomaly:
            is_anomaly = True
            ai_score = max(ai_score, ueba_score)
            detection_type = "ueba_anomaly"
            if ueba_reason:
                suggested_action = f"UEBA Anomaly: {ueba_reason}"

        return {
            "is_anomaly": is_anomaly,
            "ai_score": ai_score,
            "suggested_action": suggested_action,
            "detection_type": detection_type, # Include detection type in result
        }

    async def _automated_threat_hunt(self):
        """
        Simulates automated threat hunting by periodically scanning historical events
        against current threat intelligence.
        """
        logger.info("[EventStream] Starting automated threat hunt background task...")
        while True:
            await asyncio.sleep(60) # Run threat hunt every 60 seconds (for simulation)
            logger.debug("[EventStream] Performing automated threat hunt...")

            new_alerts_found = 0
            # Iterate through a snapshot of the event history to avoid issues with modification during iteration
            for event in list(self.event_history):
                # Re-check historical events against current threat intelligence
                ti_match = self._check_threat_intelligence(event)
                if ti_match:
                    # Check if this specific alert has already been generated to avoid duplicates
                    # In a real system, you'd store generated alerts in a DB and check against that
                    # For this simulation, we'll just log it.
                    logger.critical(
                        f"[ThreatHunt] Found historical match: {ti_match['description']} for event {event.id}"
                    )
                    new_alerts_found += 1
            if new_alerts_found > 0:
                logger.warning(f"[ThreatHunt] Completed scan. Found {new_alerts_found} new historical TI matches.")
            else:
                logger.debug("[ThreatHunt] Completed scan. No new historical TI matches found.")


    async def start(self):
        """Starts the event processing and correlation pipelines."""
        logger.info("[EventStream] Starting event stream processor...")
        asyncio.create_task(self._consume_raw_events_from_kafka()) # Start Kafka consumer
        asyncio.create_task(self._process_raw_events())
        asyncio.create_task(self._correlate_events_with_ai())
        asyncio.create_task(self._automated_threat_hunt())
        logger.info("[EventStream] Event stream processor started.")


# Example Usage (for testing)
if __name__ == "__main__":
    # Mock WebSocket Broadcaster
    async def mock_broadcast(event_json: Dict[str, Any]):
        print(f"MOCK BROADCAST: {json.dumps(event_json)}")

    # Mock PluginManager (needs to be able to load and execute anomaly detector)
    class MockPluginManager:
        def __init__(self):
            self.available_plugins = {
                "Anomaly Detector AI": {
                    "manifest": {
                        "name": "Anomaly Detector AI",
                        "entry_point": "anomaly_entry.py",  # This would be used by SandboxRunner
                        "type": "ai_module",
                        "permissions": [],
                        "sandbox_config": {},
                    },
                    "path": "plugins/anomaly_detector_ai",
                    "status": "available",
                }
            }
            # For this mock, we don't need a real SandboxRunner, we'll simulate directly

        def load_plugin(self, plugin_name):
            if plugin_name in self.available_plugins:
                self.available_plugins[plugin_name]["status"] = "loaded"
                return True
            return False

        def execute_plugin_function(
            self,
            plugin_name: str,
            function_name: str,
            *args,
            **kwargs
        ) -> Dict[str, Any]:
            if (
                plugin_name == "Anomaly Detector AI"
                and function_name == "analyze_event_for_anomaly"
            ):
                event_data = args[0]
                is_anomaly = random.random() < 0.3  # Simulate 30% chance of anomaly
                ai_score = (
                    random.uniform(0.0, 1.0) if is_anomaly else random.uniform(0.0, 0.4)
                )
                suggested_action = "MOCK Investigate" if is_anomaly else "MOCK Monitor"
                detection_type_sim = random.choice(["anomaly", "signature"]) # Simulated detection type
                return {
                    "event_id": event_data.get("id", "N/A"),
                    "timestamp": time.time(),
                    "anomaly_score": round(ai_score, 3),
                    "is_anomaly": is_anomaly,
                    "prediction_confidence": round(random.uniform(0.6, 0.95), 3),
                    "suggested_action": suggested_action,
                    "detection_type": detection_type_sim, # Include detection type
                    "simulated_by_mock_plugin": True,
                }


    mock_plugin_manager = MockPluginManager()
    
    # Create the raw event queue (this queue will now be fed by the Kafka consumer)
    raw_event_queue_instance = asyncio.Queue()

    # Create TelemetryIngestService instance
    telemetry_ingest_config_instance = TelemetryIngestConfig() # Using default config for example
    telemetry_ingest_service_instance = TelemetryIngestService(raw_event_queue=raw_event_queue_instance, config=telemetry_ingest_config_instance)

    # Create EventStreamProcessor instance, passing the raw_event_queue and telemetry_ingest_service
    processor = EventStreamProcessor(
        websocket_broadcaster=mock_broadcast,
        plugin_manager=mock_plugin_manager,
        db_session_generator=lambda: None, # Mock db_session_generator
        telemetry_ingest_service=telemetry_ingest_service_instance,
        # Pass Kafka consumer configuration
        kafka_bootstrap_servers=telemetry_ingest_config_instance.kafka_bootstrap_servers,
        raw_telemetry_topic=telemetry_ingest_config_instance.raw_telemetry_topic,
        # Pass DB configuration for mock clients
        cassandra_contact_points=telemetry_ingest_config_instance.cassandra_contact_points,
        cassandra_keyspace=telemetry_ingest_config_instance.cassandra_keyspace,
    )

    async def test_stream():
        await processor.start() # This starts _process_raw_events and _correlate_events_with_ai

        # Simulate events coming in from TelemetryIngestService (which now sends to Kafka)
        for i in range(5):
            await telemetry_ingest_service_instance.ingest_raw_log(
                log_entry=f'{{"message": "Test raw log {i}", "level": "info", "src_ip": "192.168.1.10{i}"}}',
                source="MockSensor",
            )
            await asyncio.sleep(0.1) # Small delay for producer




        # Give some time for events to be processed
        await asyncio.sleep(5)
        print("\n--- Test Stream Finished ---")

    asyncio.run(test_stream())