import asyncio
from .plugin_manager import PluginManager
from .blue_team_ai import BlueTeamAI
from .pnql_engine import PnqlEngine
from .osint_engine import OsintEngine
from .event_stream_processor import EventStreamProcessor
from .dfir_toolkit import DFIRToolkit
from .compliance_engine import ComplianceEngine
from .bas_simulator import BASSimulator
from .telemetry_ingest import TelemetryIngestService, TelemetryIngestConfig
from .database import get_db, SessionLocal, AttackLog
from log_streaming.websocket_broadcaster import broadcaster

from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends
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

def get_logs_pnql():
    db = SessionLocal()
    try:
        logs = db.query(AttackLog).order_by(AttackLog.timestamp.desc()).all()
        logger.info(f"PNQL: Retrieved {len(logs)} logs from AttackLog table.")
        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "ip": log.ip,
                "port": log.port,
                "data": log.data,
                "attack_type": log.attack_type,
                "confidence_score": log.confidence_score,
                "is_anomaly": log.is_anomaly,
                "anomaly_score": log.anomaly_score,
                "is_verified_threat": log.is_verified_threat,
                "is_blacklisted": log.is_blacklisted,
            }
            for log in logs
        ]
    finally:
        db.close()

def get_threats_pnql():
    return []

def get_assets_pnql(db: Session = Depends(get_db)): # Added db dependency
    return []

def execute_plugins_pnql(query_parsed_for_plugins: Dict[str, Any]):
    target = query_parsed_for_plugins.get("target")
    plugins_to_use = query_parsed_for_plugins.get("plugins", [])

    results = []
    for plugin_name in plugins_to_use:
        if (
            plugin_manager.available_plugins.get(plugin_name)
            and plugin_manager.available_plugins[plugin_name]["status"] != "loaded"
        ):
            plugin_manager.load_plugin(plugin_name)

        if (
            plugin_manager.available_plugins.get(plugin_name)
            and plugin_manager.available_plugins[plugin_name]["status"] == "loaded"
            and plugin_manager.available_plugins[plugin_name]["manifest"]["type"]
            == "scanner"
        ):
            print(
                f"Executing scanner plugin '{plugin_name}' on target '{target}' via PNQL."
            )
            func_name = (
                "run_kerbrute_scan"
                if "kerbrute" in plugin_name.lower()
                else "run_scanner"
            )

            plugin_result = plugin_manager.execute_plugin_function(
                plugin_name, func_name, target
            )
            results.append(
                {"plugin": plugin_name, "target": target, "result": plugin_result}
            )
        else:
            results.append(
                {
                    "plugin": plugin_name,
                    "target": target,
                    "error": "Plugin not found, not loaded, or not a scanner type.",
                }
            )
    return results

pnql_data_sources = {
    "logs": get_logs_pnql,
    "threats": get_threats_pnql,
    "assets": get_assets_pnql,
    "scan_plugins": execute_plugins_pnql,
}
pnql_engine = PnqlEngine(pnql_data_sources)

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
