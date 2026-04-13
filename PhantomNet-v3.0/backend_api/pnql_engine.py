# backend_api/pnql_engine.py
import re
import json
from typing import Dict, Any, List, Callable

class PnqlEngine:
    def __init__(self, data_sources: Dict[str, Callable]):
        """
        Initializes the PNQL Engine with available data sources.
        data_sources is a dictionary where keys are data source names (e.g., "logs", "threats")
        and values are callable functions that return data from that source.
        """
        self.data_sources = data_sources
        self.supported_commands = {
            "SELECT": self._execute_select,
            "SCAN": self._execute_scan, # Example for integrating with plugins
            "SHOW": self._execute_show, # Example for asset visibility
        }

    def _parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parses a simplified PNQL query.
        Supports:
        - SELECT <fields> FROM <source> WHERE <condition>
        - SCAN <target> WITH <plugins>
        - SHOW <assets> WHERE <condition>
        """
        query = query.strip()
        
        # Match SELECT query
        select_match = re.match(r"SELECT\s+(?P<fields>.*?)\s+FROM\s+(?P<source>\w+)(?:\s+WHERE\s+(?P<condition>.*))?", query, re.IGNORECASE)
        if select_match:
            return {
                "command": "SELECT",
                "fields": [f.strip() for f in select_match.group("fields").split(",")] if select_match.group("fields") != "*" else ["*"],
                "source": select_match.group("source"),
                "condition": select_match.group("condition")
            }
        
        # Match SCAN query
        scan_match = re.match(r"SCAN\s+(?P<target>.*?)\s+WITH\s+(?P<plugins>.*)", query, re.IGNORECASE)
        if scan_match:
            return {
                "command": "SCAN",
                "target": scan_match.group("target").strip().strip("'\""), # Remove quotes
                "plugins": [p.strip().strip("'\"") for p in scan_match.group("plugins").split(",")] # Remove quotes
            }

        # Match SHOW query
        show_match = re.match(r"SHOW\s+(?P<assets>.*?)(?:\s+WHERE\s+(?P<condition>.*))?", query, re.IGNORECASE)
        if show_match:
            return {
                "command": "SHOW",
                "assets": show_match.group("assets").strip(),
                "condition": show_match.group("condition")
            }

        raise ValueError(f"Unsupported PNQL query format: {query}")

    def _evaluate_condition(self, item: Dict[str, Any], condition: str) -> bool:
        """
        Evaluates a simple WHERE condition against a dictionary item.
        Supports basic comparisons: 'field >= value', 'field = value', 'field < value'.
        Value can be numeric or string (quoted).
        """
        if not condition:
            return True # No condition means always true

        # Simplified parsing for demo: assumes single condition for now
        match = re.match(r"(\w+)\s*([<>=!]+)\s*(.*)", condition)
        if not match:
            # Fallback for more complex conditions or unsupported syntax for demo
            print(f"Warning: Could not fully parse condition: {condition}. Skipping evaluation.")
            return True 
        
        field, operator, value_str = match.groups()
        field = field.strip()
        operator = operator.strip()
        value_str = value_str.strip()

        if field not in item:
            return False # Field not present, condition cannot be met

        item_value = item[field]

        # Attempt to convert value_str to appropriate type
        try:
            if value_str.startswith('"') and value_str.endswith('"'):
                expected_value = value_str[1:-1] # Remove quotes
            elif value_str.startswith("'") and value_str.endswith("'"):
                expected_value = value_str[1:-1] # Remove quotes
            elif value_str.lower() == "true":
                expected_value = True
            elif value_str.lower() == "false":
                expected_value = False
            elif re.fullmatch(r"[-+]?\d*\.?\d+", value_str): # Is numeric
                if '.' in value_str:
                    expected_value = float(value_str)
                else:
                    expected_value = int(value_str)
            else:
                expected_value = value_str # Treat as string if no clear type
        except ValueError:
            expected_value = value_str # Fallback to string if conversion fails

        # Perform comparison
        if operator == "=" or operator == "==":
            return item_value == expected_value
        elif operator == "!=":
            return item_value != expected_value
        elif operator == ">":
            return item_value > expected_value
        elif operator == "<":
            return item_value < expected_value
        elif operator == ">=":
            return item_value >= expected_value
        elif operator == "<=":
            return item_value <= expected_value
        
        print(f"Warning: Unsupported operator '{operator}' in condition: {condition}")
        return False # Fallback

    def _execute_select(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        source_name = parsed_query["source"]
        if source_name not in self.data_sources:
            return [{"error": f"Data source '{source_name}' not found."}]
        
        source_data = self.data_sources[source_name]() # Call the callable to get data
        if not isinstance(source_data, list):
            return [{"error": f"Data source '{source_name}' did not return a list."}]

        results = []
        for item in source_data:
            if self._evaluate_condition(item, parsed_query["condition"]):
                selected_item = {}
                if "*" in parsed_query["fields"]:
                    selected_item = item # Select all fields
                else:
                    for field in parsed_query["fields"]:
                        if field in item:
                            selected_item[field] = item[field]
                results.append(selected_item)
        return results

    def _execute_scan(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        target = parsed_query["target"]
        plugins_to_use = parsed_query["plugins"]
        
        scan_results = []
        # In a real scenario, this would interact with the PluginManager
        # to load and execute scanner plugins.
        for plugin_name in plugins_to_use:
            # Simulate plugin call
            print(f"Simulating scan on {target} with plugin: {plugin_name}")
            time.sleep(1) # Simulate scan time
            scan_results.append({
                "plugin": plugin_name,
                "target": target,
                "status": "simulated_success",
                "findings": [f"Simulated finding from {plugin_name} on {target}"]
            })
        return scan_results

    def _execute_show(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        assets_type = parsed_query["assets"]
        # This would typically query an asset management system
        print(f"Simulating showing assets of type: {assets_type}")
        time.sleep(0.5) # Simulate query time
        dummy_assets = [
            {"id": 1, "name": "Server1", "type": "server", "risk": 75, "location": "DC1"},
            {"id": 2, "name": "Workstation5", "type": "workstation", "risk": 30, "location": "OfficeA"},
            {"id": 3, "name": "RouterX", "type": "network_device", "risk": 90, "location": "DC1"},
        ]
        results = []
        for asset in dummy_assets:
            if assets_type == "*" or asset["type"] == assets_type:
                 if self._evaluate_condition(asset, parsed_query["condition"]):
                    results.append(asset)
        return results


    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Parses and executes a PNQL query."""
        try:
            parsed_query = self._parse_query(query)
            command = parsed_query["command"]
            
            if command in self.supported_commands:
                return self.supported_commands[command](parsed_query)
            else:
                return [{"error": f"Unsupported command: {command}"}]
        except ValueError as e:
            return [{"error": f"PNQL Syntax Error: {e}"}]
        except Exception as e:
            return [{"error": f"An unexpected error occurred during query execution: {e}"}]

# Example Usage
if __name__ == "__main__":
    # Dummy data sources for testing
    def get_dummy_logs():
        return [
            {"id": 1, "timestamp": "2023-11-23T10:00:00Z", "severity": "HIGH", "message": "Login failed from 192.168.1.1", "source": "auth_service"},
            {"id": 2, "timestamp": "2023-11-23T10:05:00Z", "severity": "MEDIUM", "message": "Network scan detected", "source": "ids"},
            {"id": 3, "timestamp": "2023-11-23T10:10:00Z", "severity": "CRITICAL", "message": "SQL Injection attempt", "source": "waf"},
            {"id": 4, "timestamp": "2023-11-23T10:15:00Z", "severity": "HIGH", "message": "Login failed from 192.168.1.2", "source": "auth_service"},
        ]

    def get_dummy_threats():
        return [
            {"id": "THREAT-001", "name": "DDoS Attack", "status": "active", "severity": "CRITICAL"},
            {"id": "THREAT-002", "name": "Phishing Campaign", "status": "mitigated", "severity": "HIGH"},
        ]
    
    # In a real app, 'plugins' would be linked to the PluginManager directly.
    # For this example, we'll simulate it.
    def run_simulated_plugins():
        return [{"message": "Simulated plugin output"}]


    data_sources = {
        "logs": get_dummy_logs,
        "threats": get_dummy_threats,
        "plugins": run_simulated_plugins # Placeholder
    }

    pnql_engine = PnqlEngine(data_sources)

    print("--- Testing SELECT query ---")
    query1 = "SELECT id, message FROM logs WHERE severity >= 'HIGH'"
    results1 = pnql_engine.execute_query(query1)
    print(json.dumps(results1, indent=2))

    query2 = "SELECT * FROM threats WHERE status = 'active'"
    results2 = pnql_engine.execute_query(query2)
    print(json.dumps(results2, indent=2))

    print("\n--- Testing SCAN query ---")
    query3 = "SCAN 'target.com' WITH 'Kerbrute Scanner', 'Nmap Scanner'"
    results3 = pnql_engine.execute_query(query3)
    print(json.dumps(results3, indent=2))

    print("\n--- Testing SHOW query ---")
    query4 = "SHOW assets WHERE risk > 80"
    results4 = pnql_engine.execute_query(query4)
    print(json.dumps(results4, indent=2))

    query5 = "SHOW network_device"
    results5 = pnql_engine.execute_query(query5)
    print(json.dumps(results5, indent=2))

    print("\n--- Testing invalid query ---")
    query_invalid = "FETCH data"
    results_invalid = pnql_engine.execute_query(query_invalid)
    print(json.dumps(results_invalid, indent=2))

    print("\n--- Testing unknown source ---")
    query_unknown_source = "SELECT * FROM non_existent_source"
    results_unknown_source = pnql_engine.execute_query(query_unknown_source)
    print(json.dumps(results_unknown_source, indent=2))
