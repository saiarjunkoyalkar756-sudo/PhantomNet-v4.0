# backend_api/cassandra_client.py
from loguru import logger
from typing import List, Dict, Any, Optional
import json

from .schemas import RawEvent, NormalizedEvent
from backend_api.core_config import SAFE_MODE

# Conditional import for Cassandra
if not SAFE_MODE:
    from cassandra.cluster import Cluster, ResultSet, Session
    from cassandra.auth import PlainTextAuthProvider
    from cassandra.query import BatchStatement, SimpleStatement
    from cassandra import ConsistencyLevel
else:
    # Define dummy classes if SAFE_MODE is enabled to prevent ModuleNotFoundError
    class Cluster:
        def __init__(self, *args, **kwargs):
            logger.warning("SAFE_MODE: Cassandra Cluster is a dummy object.")
        def connect(self, *args, **kwargs):
            return DummySession()
        def shutdown(self):
            pass

    class DummySession:
        def execute(self, *args, **kwargs):
            logger.warning("SAFE_MODE: Dummy Cassandra Session execute called.")
            return []
        def set_keyspace(self, *args, **kwargs):
            pass
        def prepare(self, *args, **kwargs):
            return DummyPreparedStatement()

    class DummyPreparedStatement:
        pass

    class ResultSet:
        pass

    class Session:
        pass
    
    class PlainTextAuthProvider:
        def __init__(self, *args, **kwargs):
            pass
    
    class BatchStatement:
        def __init__(self, *args, **kwargs):
            pass

    class SimpleStatement:
        def __init__(self, *args, **kwargs):
            pass

    class ConsistencyLevel:
        ONE = None

class CassandraClient:
    def __init__(
        self,
        contact_points: List[str],
        keyspace: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        replication_factor: int = 1,
    ):
        self.contact_points = contact_points
        self.keyspace = keyspace
        self.replication_factor = replication_factor
        self.username = username
        self.password = password
        self.cluster: Optional[Cluster] = None
        self.session: Optional[Session] = None
        self._connect()

    def _connect(self):
        if SAFE_MODE:
            logger.warning("SAFE_MODE is ON. Cassandra persistence layer is disabled.")
            self.cluster = None
            self.session = None
            return

        try:
            auth_provider = None
            if self.username and self.password:
                auth_provider = PlainTextAuthProvider(
                    username=self.username, password=self.password
                )

            self.cluster = Cluster(
                self.contact_points,
                auth_provider=auth_provider,
                protocol_version=5 # Ensure compatibility
            )
            self.session = self.cluster.connect()
            logger.info(
                f"Connected to Cassandra cluster at {', '.join(self.contact_points)}"
            )
            self._create_keyspace_and_tables()
        except Exception as e:
            logger.warning(f"Cassandra unavailable, disabling persistence layer: {e}")
            self.cluster = None
            self.session = None

    def _create_keyspace_and_tables(self):
        if not self.session:
            logger.warning("Cassandra session not established, skipping schema creation.")
            return

        # Create Keyspace
        self.session.execute(
            f"""
            CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': {self.replication_factor}}}
            AND durable_writes = true;
            """
        )
        self.session.set_keyspace(self.keyspace)
        logger.info(f"Keyspace '{self.keyspace}' ensured and set.")

        # Create raw_telemetry table
        self.session.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_telemetry (
                id UUID PRIMARY KEY,
                timestamp TIMESTAMP,
                source TEXT,
                type TEXT,
                data TEXT,
                raw_log TEXT
            );
            """
        )
        logger.info("Table 'raw_telemetry' ensured.")

        # Create normalized_telemetry table
        self.session.execute(
            """
            CREATE TABLE IF NOT EXISTS normalized_telemetry (
                event_id UUID PRIMARY KEY,
                timestamp TIMESTAMP,
                source TEXT,
                event_type TEXT,
                raw_data TEXT,
                host_name TEXT,
                user_name TEXT,
                src_ip TEXT,
                dest_ip TEXT,
                src_port INT,
                dest_port INT,
                process_name TEXT,
                file_path TEXT,
                metadata TEXT
            );
            """
        )
        logger.info("Table 'normalized_telemetry' ensured.")

        self.insert_raw_telemetry_stmt = self.session.prepare(
            """
            INSERT INTO raw_telemetry (id, timestamp, source, type, data, raw_log)
            VALUES (?, ?, ?, ?, ?, ?)
            """
        )
        self.insert_normalized_telemetry_stmt = self.session.prepare(
            """
            INSERT INTO normalized_telemetry (event_id, timestamp, source, event_type, raw_data, host_name, user_name, src_ip, dest_ip, src_port, dest_port, process_name, file_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        )
        logger.info("Prepared statements for telemetry insertion.")

    def save_raw_event(self, event: RawEvent):
        if not self.session:
            logger.warning("Cassandra offline — skipping persistence for RawEvent.")
            return
        try:
            self.session.execute(
                self.insert_raw_telemetry_stmt,
                (
                    event.id,
                    event.timestamp,
                    event.source,
                    event.type,
                    json.dumps(event.data),
                    event.raw_log,
                ),
            )
            logger.debug(f"Saved RawEvent {event.id} to Cassandra.")
        except Exception as e:
            logger.error(f"Failed to save RawEvent {event.id} to Cassandra: {e}")
            raise

    def save_normalized_event(self, event: NormalizedEvent):
        if not self.session:
            logger.warning("Cassandra offline — skipping persistence for NormalizedEvent.")
            return
        try:
            self.session.execute(
                self.insert_normalized_telemetry_stmt,
                (
                    event.event_id,
                    event.timestamp,
                    event.source,
                    event.event_type,
                    event.raw_data,
                    event.host_name,
                    event.user_name,
                    event.src_ip,
                    event.dest_ip,
                    event.src_port,
                    event.dest_port,
                    event.process_name,
                    event.file_path,
                    json.dumps(event.metadata),
                ),
            )
            logger.debug(f"Saved NormalizedEvent {event.event_id} to Cassandra.")
        except Exception as e:
            logger.error(
                f"Failed to save NormalizedEvent {event.event_id} to Cassandra: {e}"
            )
            raise

    def shutdown(self):
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Cassandra cluster connection shut down.")


if __name__ == "__main__":
    # Example Usage
    from datetime import datetime
    import uuid

    logger.remove()
    logger.add(lambda msg: print(msg), level="INFO")

    # Assuming a Cassandra instance is running locally on default port 9042
    # For a real setup, provide correct contact_points and authentication
    client = None
    try:
        client = CassandraClient(
            contact_points=["127.0.0.1"],
            keyspace="test_phantomnet_telemetry",
            replication_factor=1,
            # username="cassandra", password="cassandra" # If authentication is enabled
        )

        # Test RawEvent persistence
        test_raw_event = RawEvent(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            source="test_source",
            type="test_raw_log",
            data={"key": "value", "level": "info"},
            raw_log="This is a raw test log entry.",
        )
        client.save_raw_event(test_raw_event)

        # Test NormalizedEvent persistence
        test_normalized_event = NormalizedEvent(
            event_id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            source="test_source",
            event_type="test_normalized_event",
            raw_data="Raw data string for normalized event.",
            host_name="test_host",
            user_name="test_user",
            src_ip="192.168.1.1",
            dest_ip="10.0.0.1",
            metadata={"enriched": True, "prio": 1},
        )
        client.save_normalized_event(test_normalized_event)

        logger.info("Test data saved to Cassandra successfully.")

    except Exception as e:
        logger.error(f"An error occurred during Cassandra client test: {e}")
    finally:
        if client:
            client.shutdown()
