# backend_api/test_pnql_engine.py
import unittest
import json
from .pnql_engine import PnqlEngine


# Dummy data sources for testing
def get_dummy_logs():
    return [
        {
            "id": 1,
            "timestamp": "2023-11-23T10:00:00Z",
            "severity": "HIGH",
            "message": "Login failed from 192.168.1.1",
            "source": "auth_service",
        },
        {
            "id": 2,
            "timestamp": "2023-11-23T10:05:00Z",
            "severity": "MEDIUM",
            "message": "Network scan detected",
            "source": "ids",
        },
        {
            "id": 3,
            "timestamp": "2023-11-23T10:10:00Z",
            "severity": "CRITICAL",
            "message": "SQL Injection attempt",
            "source": "waf",
        },
        {
            "id": 4,
            "timestamp": "2023-11-23T10:15:00Z",
            "severity": "HIGH",
            "message": "Login failed from 192.168.1.2",
            "source": "auth_service",
        },
    ]


def get_dummy_threats():
    return [
        {
            "id": "THREAT-001",
            "name": "DDoS Attack",
            "status": "active",
            "severity": "CRITICAL",
        },
        {
            "id": "THREAT-002",
            "name": "Phishing Campaign",
            "status": "mitigated",
            "severity": "HIGH",
        },
    ]


def get_dummy_processes():
    return [
        {
            "pid": 101,
            "name": "chrome.exe",
            "cpu": 15.2,
            "memory": 256.4,
            "parent": "explorer.exe",
        },
        {
            "pid": 102,
            "name": "svchost.exe",
            "cpu": 0.3,
            "memory": 50.1,
            "parent": "services.exe",
        },
        {
            "pid": 103,
            "name": "cmd.exe",
            "cpu": 0.1,
            "memory": 4.2,
            "parent": "explorer.exe",
        },
        {
            "pid": 104,
            "name": "powershell.exe",
            "cpu": 1.1,
            "memory": 25.8,
            "parent": "cmd.exe",
        },
    ]


class TestPnqlEngine(unittest.TestCase):

    def setUp(self):
        data_sources = {
            "logs": get_dummy_logs,
            "threats": get_dummy_threats,
            "processes": get_dummy_processes,
        }
        self.pnql_engine = PnqlEngine(data_sources)

    def test_select_query_with_high_severity(self):
        query = "SELECT id, message FROM logs WHERE severity = 'HIGH'"
        results = self.pnql_engine.execute_query(query)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], 1)
        self.assertEqual(results[1]["id"], 4)

    def test_scan_query(self):
        query = 'SCAN domain("example.com") USING "Nmap", "Nikto"'
        results = self.pnql_engine.execute_query(query)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["plugin"], "Nmap")
        self.assertEqual(results[0]["target"], "domain(example.com)")
        self.assertEqual(results[1]["plugin"], "Nikto")
        self.assertEqual(results[1]["target"], "domain(example.com)")

    def test_show_query_with_condition(self):
        query = "SHOW processes WHERE parent = 'cmd.exe'"
        results = self.pnql_engine.execute_query(query)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["pid"], 104)

    def test_show_query_without_condition(self):
        query = "SHOW processes"
        results = self.pnql_engine.execute_query(query)
        self.assertEqual(len(results), 4)

    def test_show_assets_summary(self):
        query = "SHOW assets"
        results = self.pnql_engine.execute_query(query)
        self.assertEqual(len(results), 1)
        self.assertIn("available_asset_types", results[0])
        self.assertIn("logs", results[0]["available_asset_types"])
        self.assertIn("threats", results[0]["available_asset_types"])
        self.assertIn("processes", results[0]["available_asset_types"])

    def test_invalid_query(self):
        query = "INVALID QUERY"
        results = self.pnql_engine.execute_query(query)
        self.assertEqual(len(results), 1)
        self.assertIn("error", results[0])
        self.assertIn("Unsupported PNQL query format", results[0]["error"])


if __name__ == "__main__":
    unittest.main()
