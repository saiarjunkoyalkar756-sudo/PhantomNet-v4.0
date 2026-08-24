import asyncio
from .plugin_manager import PluginManager
from .blue_team_ai import BlueTeamAI
from .osint_engine import OsintEngine
from .event_stream_processor import EventStreamProcessor
from .dfir_toolkit import DFIRToolkit
from .compliance_engine import ComplianceEngine
from .bas_simulator import BASSimulator
from .telemetry_ingest import TelemetryIngestService, TelemetryIngestConfig
from .database import get_db
from backend_api.log_streaming.websocket_broadcaster import broadcaster

from typing import Dict
from loguru import logger

# Dictionary to hold background tasks
background_tasks: Dict[str, asyncio.Task] = {}

# Initialize all services here
plugin_manager = PluginManager()
blue_team_ai = BlueTeamAI(plugin_manager)
osint_engine = OsintEngine()

telemetry_ingest_config_instance = TelemetryIngestConfig()
raw_event_queue_instance = asyncio.Queue()
telemetry_ingest_service_instance = TelemetryIngestService(raw_event_queue=raw_event_queue_instance, config=telemetry_ingest_config_instance)

event_stream_processor = EventStreamProcessor(
    websocket_broadcaster=broadcaster.broadcast,
    plugin_manager=plugin_manager,
    db_session_generator=get_db,
    telemetry_ingest_service=telemetry_ingest_service_instance,
    kafka_bootstrap_servers=telemetry_ingest_config_instance.kafka_bootstrap_servers,
    raw_telemetry_topic=telemetry_ingest_config_instance.raw_telemetry_topic,
    cassandra_contact_points=telemetry_ingest_config_instance.cassandra_contact_points,
    cassandra_keyspace=telemetry_ingest_config_instance.cassandra_keyspace,
)

dfir_toolkit = DFIRToolkit()
compliance_engine = ComplianceEngine()
bas_simulator = BASSimulator()




def get_telemetry_ingest_service() -> TelemetryIngestService:
    return event_stream_processor.telemetry_ingest_service

async def start_services():
    logger.info("Starting background services...")
    background_tasks["blue_team_ai"] = asyncio.create_task(blue_team_ai.run_defense_cycle())
    background_tasks["event_stream_processor"] = asyncio.create_task(event_stream_processor.start())
    logger.info("Background services started.")

async def stop_services():
    # Graceful shutdown of services can be implemented here
    logger.info("Stopping background services...")
    for name, task in background_tasks.items():
        task.cancel()
        logger.info(f"Cancelled background service: {name}")
    await asyncio.gather(*background_tasks.values(), return_exceptions=True)
    logger.info("All background services stopped.")

def is_service_running(name: str) -> bool:
    """Checks if a background service task is running."""
    task = background_tasks.get(name)
    if task:
        return not task.done()
    return False
