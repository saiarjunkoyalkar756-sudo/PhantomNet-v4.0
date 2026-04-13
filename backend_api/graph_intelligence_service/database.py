# backend_api/graph_intelligence_service/database.py

from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def query(self, query, parameters=None, db=None):
        with self._driver.session(database=db) as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def get_connection(self):
        return self._driver

import os

# ... (rest of the imports)

# ... (Neo4jConnection class)

# Global connection
conn = None

def get_db_connection():
    global conn
    if conn is None:
        # These should be loaded from config
        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD") # No default for password
        if not password:
            raise ValueError("NEO4J_PASSWORD environment variable not set.")
        conn = Neo4jConnection(uri, user, password)
    return conn

if __name__ == "__main__":
    db_conn = get_db_connection()
    # Simple query to test connection
    results = db_conn.query("MATCH (n) RETURN count(n) AS count")
    print(f"Node count: {results[0]['count']}")
    db_conn.close()
