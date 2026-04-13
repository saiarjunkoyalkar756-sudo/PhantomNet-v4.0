# backend_api/siem_integration_service/phantomql_engine.py

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from shared.logger_config import logger
from .schemas import NormalizedLog, PhantomQLQuery, QueryResult # Import models

logger = logger

class PhantomQLEngine:
    """
    A conceptual query engine (PhantomQL) for normalized log data.
    In a real SIEM, this would interface with a time-series database (e.g., Elasticsearch, ClickHouse, Splunk).
    For now, it simulates querying against an in-memory list of logs.
    """
    def __init__(self):
        self.indexed_logs: List[NormalizedLog] = [] # In-memory store of "indexed" normalized logs
        logger.info("PhantomQLEngine initialized.")

    def _apply_filters(self, log: NormalizedLog, query_params: Dict[str, Any]) -> bool:
        """Applies filters from query_params to a single NormalizedLog."""
        if query_params.get("event_type") and log.event_type != query_params["event_type"]:
            return False
        if query_params.get("host_id") and log.host_id != query_params["host_id"]:
            return False
        if query_params.get("source_ip") and log.source_ip != query_params["source_ip"]:
            return False
        if query_params.get("message_contains") and query_params["message_contains"].lower() not in log.message.lower():
            return False
        if query_params.get("severity") and log.severity != query_params["severity"]:
            return False
        
        # Add more filter logic here for other fields and operators
        return True

    async def query_logs(self, phantomql_query: PhantomQLQuery) -> QueryResult:
        """
        Executes a PhantomQL query against the indexed logs.
        This is a conceptual implementation of a query.
        """
        logger.info(f"Executing PhantomQL query: {phantomql_query.query_string}")
        await asyncio.sleep(0.5) # Simulate query time

        # For demonstration, we'll parse a very simple query string
        # In a real system, a robust parser for PhantomQL would be needed.
        # Example PhantomQL: "event_type='process.create' AND host_id='server-1'"
        
        # Simple parsing for key-value pairs
        query_params = {}
        parts = phantomql_query.query_string.split(" AND ")
        for part in parts:
            if "='" in part and part.endswith("'"):
                key, value = part.split("='", 1)
                query_params[key] = value[:-1] # Remove trailing '
            elif "=" in part: # For numeric/boolean, handle more robustly
                key, value = part.split("=", 1)
                query_params[key] = value
        
        # Apply time range filters
        filtered_logs = [
            log for log in self.indexed_logs
            if (not phantomql_query.time_range_start or log.timestamp >= phantomql_query.time_range_start) and
               (not phantomql_query.time_range_end or log.timestamp <= phantomql_query.time_range_end) and
               self._apply_filters(log, query_params)
        ]
        
        total_hits = len(filtered_logs)
        
        # Apply limit and offset
        start_index = phantomql_query.offset
        end_index = start_index + phantomql_query.limit
        paginated_logs = filtered_logs[start_index:end_index]

        logger.info(f"PhantomQL query '{phantomql_query.query_string}' executed. Found {total_hits} hits.")
        
        return QueryResult(
            total_hits=total_hits,
            took_ms=int(0.5 * 1000), # Simulated
            logs=paginated_logs
        )

    def add_indexed_log(self, log: NormalizedLog):
        """Adds a normalized log to the in-memory index."""
        self.indexed_logs.append(log)
        # In a real system, this would push to Elasticsearch/Splunk etc.

# Example usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running PhantomQLEngine example...")
    
    # Needs uuid import
    import uuid

    async def run_example():
        engine = PhantomQLEngine()

        # Add some mock normalized logs
        engine.add_indexed_log(NormalizedLog(
            event_id=str(uuid.uuid4()), timestamp=datetime.utcnow(), event_type="process.create",
            source_system="agent-linux", host_id="server-1", message="Process 'bash' created by user 'root'",
            full_data={"process_name": "bash", "user": "root", "pid": 1234}
        ))
        engine.add_indexed_log(NormalizedLog(
            event_id=str(uuid.uuid4()), timestamp=datetime.utcnow() - timedelta(minutes=5), event_type="network.connection",
            source_system="agent-windows", host_id="workstation-1", message="Connection from 192.168.1.100 to 8.8.8.8:53",
            source_ip="192.168.1.100", destination_ip="8.8.8.8", destination_port=53, network_protocol="udp",
            full_data={"src_ip": "192.168.1.100", "dst_ip": "8.8.8.8"}
        ))
        engine.add_indexed_log(NormalizedLog(
            event_id=str(uuid.uuid4()), timestamp=datetime.utcnow() - timedelta(minutes=10), event_type="auth.login",
            source_system="firewall", host_id="firewall-gw", message="Failed login attempt for user 'baduser' from 1.1.1.1",
            source_ip="1.1.1.1", severity="warning",
            full_data={"user": "baduser", "action": "login_failed"}
        ))

        # Test simple query
        query1 = PhantomQLQuery(query_string="event_type='process.create'")
        result1 = await engine.query_logs(query1)
        logger.info(f"\nQuery 1 Result (process.create):\n{json.dumps([log.model_dump() for log in result1.logs], indent=2)}")

        # Test query with multiple filters
        query2 = PhantomQLQuery(query_string="source_ip='1.1.1.1' AND severity='warning'", limit=1)
        result2 = await engine.query_logs(query2)
        logger.info(f"\nQuery 2 Result (source_ip & severity):\n{json.dumps([log.model_dump() for log in result2.logs], indent=2)}")

        # Test time-range query (conceptual - as current logs use utcnow)
        query3 = PhantomQLQuery(query_string="event_type='network.connection'", time_range_start=datetime.utcnow() - timedelta(minutes=6))
        result3 = await engine.query_logs(query3)
        logger.info(f"\nQuery 3 Result (time-range):\n{json.dumps([log.model_dump() for log in result3.logs], indent=2)}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("PhantomQLEngine example stopped.")
