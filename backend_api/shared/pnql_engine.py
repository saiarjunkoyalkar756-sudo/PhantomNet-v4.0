import re
import json
import time
import logging # Import logging
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger(__name__) # Initialize logger for this module


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
            "SCAN": self._execute_scan,  # Example for integrating with plugins
            "SHOW": self._execute_show,  # Example for asset visibility
        }

    def _parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parses a simplified PNQL query.
        Supports:
        - SELECT <fields> FROM <source> WHERE <condition> (with AND/OR and LIKE)
        - SCAN <target> WITH <plugins>
        - SHOW <assets> WHERE <condition>
        """
        query = query.strip()

        # Match SELECT query
        select_match = re.match(
            r"SELECT\s+(?P<fields>.*?)\s+FROM\s+(?P<source>\w+)(?:\s+WHERE\s+(?P<condition>.*))?",
            query,
            re.IGNORECASE,
        )
        if select_match:
            fields_str = select_match.group("fields")
            fields = []
            aggregations = []

            # Regex to find aggregation functions
            aggregation_pattern = re.compile(r"(COUNT|SUM|AVG|MIN|MAX)\((.*?)\)", re.IGNORECASE)
            
            remaining_fields = fields_str
            for agg_match in aggregation_pattern.finditer(fields_str):
                agg_func = agg_match.group(1).upper()
                agg_field = agg_match.group(2).strip()
                aggregations.append({"function": agg_func, "field": agg_field if agg_field != "*" else None})
                # Remove the matched aggregation from the string
                remaining_fields = remaining_fields.replace(agg_match.group(0), "").strip()

            # Process remaining non-aggregation fields
            if remaining_fields:
                fields = [f.strip() for f in remaining_fields.split(",") if f.strip()]
                if "*" in fields: # If '*' is present, it means select all non-aggregated fields
                    fields = ["*"]

            return {
                "command": "SELECT",
                "fields": fields,
                "aggregations": aggregations,
                "source": select_match.group("source"),
                "condition": select_match.group("condition"),
            }

        # Match SCAN query
        scan_match = re.match(
            r"SCAN\s+(?P<target_func>\w+)\((?P<target_value>.*?)\)\s+USING\s+(?P<plugins>.*)",
            query,
            re.IGNORECASE,
        )
        if scan_match:
            return {
                "command": "SCAN",
                "target_func": scan_match.group("target_func").strip(),
                "target_value": scan_match.group("target_value")
                .strip()
                .strip("'\""),  # Remove quotes
                "plugins": [
                    p.strip().strip("'\"")
                    for p in scan_match.group("plugins").split(",")
                ],  # Remove quotes
            }

        # Match SHOW query
        show_match = re.match(
            r"SHOW\s+(?P<assets>\w+)(?:\s+WHERE\s+(?P<condition>.*))?",
            query,
            re.IGNORECASE,
        )
        if show_match:
            return {
                "command": "SHOW",
                "assets": show_match.group("assets").strip(),
                "condition": show_match.group("condition"),
            }

        raise ValueError(f"Unsupported PNQL query format: {query}")

    def _evaluate_single_condition(self, item: Dict[str, Any], condition_str: str) -> bool:
        """
        Evaluates a single WHERE condition against a dictionary item.
        Supports basic comparisons: 'field >= value', 'field = value', 'field < value', 'field LIKE "pattern"'.
        """
        # Operators and their regex patterns
        operators = {
            "==": r"==",
            "!=": r"!=",
            ">=": r">=",
            "<=": r"<=",
            ">": r">",
            "<": r"<",
            "LIKE": r"LIKE",
        }
        
        # Build a regex to match any of the operators
        op_pattern = "|".join(re.escape(op) for op in operators.values())
        match = re.match(fr"(\w+)\s*({op_pattern})\s*(.*)", condition_str, re.IGNORECASE)

        if not match:
            logger.warning(f"Could not parse single condition: {condition_str}. Assuming false.")
            return False

        field, operator_str, value_str = match.groups()
        field = field.strip()
        operator_str = operator_str.strip().upper() # Normalize operator for LIKE

        if field not in item:
            return False

        item_value = item[field]

        # Attempt to convert value_str to appropriate type
        try:
            if (value_str.startswith('"') and value_str.endswith('"')) or \
               (value_str.startswith("'") and value_str.endswith("'")):
                expected_value = value_str[1:-1]
            elif value_str.lower() == "true":
                expected_value = True
            elif value_str.lower() == "false":
                expected_value = False
            elif re.fullmatch(r"[-+]?\d*\.?\d+", value_str):
                expected_value = float(value_str) if "." in value_str else int(value_str)
            else:
                expected_value = value_str
        except ValueError:
            expected_value = value_str
        
        # Perform comparison
        if operator_str == "==":
            return item_value == expected_value
        elif operator_str == "!=":
            return item_value != expected_value
        elif operator_str == ">":
            return item_value > expected_value
        elif operator_str == "<":
            return item_value < expected_value
        elif operator_str == ">=":
            return item_value >= expected_value
        elif operator_str == "<=":
            return item_value <= expected_value
        elif operator_str == "LIKE":
            if isinstance(item_value, str) and isinstance(expected_value, str):
                # Convert SQL-like % and _ wildcards to regex .* and .
                regex_pattern = expected_value.replace("%", ".*").replace("_", ".")
                return re.search(regex_pattern, item_value, re.IGNORECASE) is not None
            return False

        logger.warning(f"Unsupported operator '{operator_str}' in condition: {condition_str}")
        return False

    def _evaluate_condition(self, item: Dict[str, Any], condition: Optional[str]) -> bool:
        """
        Recursively evaluates a WHERE condition against a dictionary item,
        supporting AND/OR logic and parentheses.
        """
        if not condition:
            return True

        condition = condition.strip()

        # Handle parentheses
        # This is a simplified approach and might not handle nested parentheses perfectly in a single pass.
        # A proper parser (e.g., using pyparsing) would be better for complex grammar.
        # For this demo, we'll try to resolve the outermost parentheses first.
        parentheses_match = re.search(r"\(([^()]*)\)", condition)
        while parentheses_match:
            sub_condition_str = parentheses_match.group(1)
            # Evaluate the sub-condition and replace it with a boolean literal
            sub_result = self._evaluate_condition(item, sub_condition_str)
            condition = condition.replace(f"({sub_condition_str})", " True " if sub_result else " False ", 1)
            parentheses_match = re.search(r"\(([^()]*)\)", condition) # Rescan for remaining parentheses

        # Evaluate AND/OR. Process ORs last due to operator precedence.
        if " OR " in condition.upper():
            or_parts = re.split(r'\s+OR\s+', condition, flags=re.IGNORECASE)
            return any(self._evaluate_condition(item, part.strip()) for part in or_parts)
        elif " AND " in condition.upper():
            and_parts = re.split(r'\s+AND\s+', condition, flags=re.IGNORECASE)
            return all(self._evaluate_condition(item, part.strip()) for part in and_parts)
        else:
            # If no AND/OR, it's a single condition or a boolean literal from parentheses evaluation
            if condition.strip().lower() == "true":
                return True
            if condition.strip().lower() == "false":
                return False
            return self._evaluate_single_condition(item, condition)

    def _execute_select(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        source_name = parsed_query["source"]
        if source_name not in self.data_sources:
            return [{"error": f"Data source '{source_name}' not found."}]

        source_data = self.data_sources[source_name]()  # Call the callable to get data
        if not isinstance(source_data, list):
            return [{"error": f"Data source '{source_name}' did not return a list."}]

        filtered_items = []
        for item in source_data:
            if self._evaluate_condition(item, parsed_query["condition"]):
                filtered_items.append(item)
        
        aggregations_to_perform = parsed_query.get("aggregations", [])
        if aggregations_to_perform:
            aggregation_results = {}
            for agg in aggregations_to_perform:
                agg_func = agg["function"]
                agg_field = agg["field"]

                if agg_func == "COUNT":
                    if agg_field is None: # COUNT(*)
                        aggregation_results["count"] = len(filtered_items)
                    else:
                        aggregation_results[f"count_{agg_field}"] = sum(1 for item in filtered_items if agg_field in item)
                elif agg_func == "SUM":
                    if agg_field:
                        sum_val = sum(item.get(agg_field, 0) for item in filtered_items if isinstance(item.get(agg_field), (int, float)))
                        aggregation_results[f"sum_{agg_field}"] = sum_val
                elif agg_func == "AVG":
                    if agg_field:
                        numeric_values = [item.get(agg_field) for item in filtered_items if isinstance(item.get(agg_field), (int, float))]
                        if numeric_values:
                            aggregation_results[f"avg_{agg_field}"] = sum(numeric_values) / len(numeric_values)
                        else:
                            aggregation_results[f"avg_{agg_field}"] = None
                elif agg_func == "MIN":
                    if agg_field:
                        numeric_values = [item.get(agg_field) for item in filtered_items if isinstance(item.get(agg_field), (int, float))]
                        if numeric_values:
                            aggregation_results[f"min_{agg_field}"] = min(numeric_values)
                        else:
                            aggregation_results[f"min_{agg_field}"] = None
                elif agg_func == "MAX":
                    if agg_field:
                        numeric_values = [item.get(agg_field) for item in filtered_items if isinstance(item.get(agg_field), (int, float))]
                        if numeric_values:
                            aggregation_results[f"max_{agg_field}"] = max(numeric_values)
                        else:
                            aggregation_results[f"max_{agg_field}"] = None
            return [aggregation_results]
        else:
            results = []
            for item in filtered_items:
                selected_item = {}
                if "*" in parsed_query["fields"]:
                    selected_item = item  # Select all fields
                else:
                    for field in parsed_query["fields"]:
                        if field in item:
                            selected_item[field] = item[field]
                results.append(selected_item)
            return results

    def _execute_scan(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_func = parsed_query["target_func"]
        target_value = parsed_query["target_value"]
        plugins_to_use = parsed_query["plugins"]

        target = f"{target_func}({target_value})"

        scan_results = []
        # In a real scenario, this would interact with the PluginManager
        # to load and execute scanner plugins.
        for plugin_name in plugins_to_use:
            # Simulate plugin call
            print(f"Simulating scan on {target} with plugin: {plugin_name}")
            time.sleep(1)  # Simulate scan time
            scan_results.append(
                {
                    "plugin": plugin_name,
                    "target": target,
                    "status": "simulated_success",
                    "findings": [f"Simulated finding from {plugin_name} on {target}"],
                }
            )
        return scan_results

    def _execute_show(self, parsed_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        assets_type = parsed_query.get("assets", "").lower()

        if assets_type == "assets":
            return [
                {
                    "available_asset_types": sorted(
                        [k for k in self.data_sources.keys() if k != "plugins"]
                    )
                }
            ]

        if not assets_type or assets_type not in self.data_sources:
            return [{"error": f"Data source for asset type '{assets_type}' not found."}]

        source_data = self.data_sources[assets_type]()
        if not isinstance(source_data, list):
            return [{"error": f"Data source '{assets_type}' did not return a list."}]

        results = []
        condition = parsed_query.get("condition")
        for item in source_data:
            if self._evaluate_condition(item, condition):
                results.append(item)
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
            return [
                {"error": f"An unexpected error occurred during query execution: {e}"}
            ]


# Example Usage
if __name__ == "__main__":
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
            {
                "id": 5,
                "timestamp": "2023-11-23T10:20:00Z",
                "severity": "LOW",
                "message": "User 'admin' accessed report",
                "source": "report_service",
            },
            {
                "id": 6,
                "timestamp": "2023-11-23T10:25:00Z",
                "severity": "MEDIUM",
                "message": "Failed login attempt from 10.0.0.1",
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
            {
                "id": "THREAT-003",
                "name": "Malware Infection",
                "status": "active",
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

    # In a real app, 'plugins' would be linked to the PluginManager directly.
    def run_simulated_plugins():
        return [{"message": "Simulated plugin output"}]

    data_sources = {
        "logs": get_dummy_logs,
        "threats": get_dummy_threats,
        "processes": get_dummy_processes,
        "plugins": run_simulated_plugins,
    }

    pnql_engine = PnqlEngine(data_sources)

    print("--- Testing SELECT query with LIKE ---")
    query1_like = "SELECT id, message FROM logs WHERE message LIKE '%Login failed%'"
    results1_like = pnql_engine.execute_query(query1_like)
    print(json.dumps(results1_like, indent=2))

    print("\n--- Testing SELECT query with AND ---")
    query_and = "SELECT id, message, severity FROM logs WHERE severity = 'HIGH' AND source = 'auth_service'"
    results_and = pnql_engine.execute_query(query_and)
    print(json.dumps(results_and, indent=2))

    print("\n--- Testing SELECT query with OR ---")
    query_or = "SELECT id, message, severity FROM logs WHERE severity = 'CRITICAL' OR source = 'ids'"
    results_or = pnql_engine.execute_query(query_or)
    print(json.dumps(results_or, indent=2))

    print("\n--- Testing SELECT query with AND and OR ---")
    query_and_or = "SELECT id, message FROM logs WHERE (severity = 'HIGH' AND source = 'auth_service') OR severity = 'CRITICAL'"
    results_and_or = pnql_engine.execute_query(query_and_or)
    print(json.dumps(results_and_or, indent=2))

    print("\n--- Testing SELECT query with parentheses ---")
    query_parentheses = "SELECT id, message FROM logs WHERE message LIKE '%failed%' AND (source = 'auth_service' OR source = 'ids')"
    results_parentheses = pnql_engine.execute_query(query_parentheses)
    print(json.dumps(results_parentheses, indent=2))

    print("\n--- Testing original SELECT query ---")
    query1 = "SELECT id, message FROM logs WHERE severity >= 'HIGH'"
    results1 = pnql_engine.execute_query(query1)
    print(json.dumps(results1, indent=2))

    query2 = "SELECT * FROM threats WHERE status = 'active'"
    results2 = pnql_engine.execute_query(query2)
    print(json.dumps(results2, indent=2))

    print("\n--- Testing SCAN query ---")
    query3 = 'SCAN domain("target.com") USING "Kerbrute Scanner", "Nmap Scanner"'
    results3 = pnql_engine.execute_query(query3)
    print(json.dumps(results3, indent=2))

    print("\n--- Testing SHOW query (specific)---")
    query4 = "SHOW processes WHERE parent = 'cmd.exe'"
    results4 = pnql_engine.execute_query(query4)
    print(json.dumps(results4, indent=2))

    print("\n--- Testing SHOW query (all)---")
    query5 = "SHOW processes"
    results5 = pnql_engine.execute_query(query5)
    print(json.dumps(results5, indent=2))

    print("\n--- Testing SHOW query (assets summary)---")
    query6 = "SHOW assets"
    results6 = pnql_engine.execute_query(query6)
    print(json.dumps(results6, indent=2))

    print("\n--- Testing invalid query ---")
    query_invalid = "FETCH data"
    results_invalid = pnql_engine.execute_query(query_invalid)
    print(json.dumps(results_invalid, indent=2))

    print("\n--- Testing SELECT query with COUNT(*) ---")
    query_count_all = "SELECT COUNT(*) FROM logs WHERE severity = 'HIGH'"
    results_count_all = pnql_engine.execute_query(query_count_all)
    print(json.dumps(results_count_all, indent=2))

    print("\n--- Testing SELECT query with COUNT(id) ---")
    query_count_id = "SELECT COUNT(id) FROM logs WHERE source = 'auth_service'"
    results_count_id = pnql_engine.execute_query(query_count_id)
    print(json.dumps(results_count_id, indent=2))

    print("\n--- Testing SELECT query with SUM(cpu) ---")
    query_sum_cpu = "SELECT SUM(cpu) FROM processes WHERE parent = 'explorer.exe'"
    results_sum_cpu = pnql_engine.execute_query(query_sum_cpu)
    print(json.dumps(results_sum_cpu, indent=2))

    print("\n--- Testing SELECT query with AVG(memory) ---")
    query_avg_mem = "SELECT AVG(memory) FROM processes"
    results_avg_mem = pnql_engine.execute_query(query_avg_mem)
    print(json.dumps(results_avg_mem, indent=2))

    print("\n--- Testing SELECT query with MIN(severity) (will return 0 as str comparison) ---")
    query_min_severity = "SELECT MIN(severity) FROM logs"
    results_min_severity = pnql_engine.execute_query(query_min_severity)
    print(json.dumps(results_min_severity, indent=2))

    print("\n--- Testing SELECT query with MAX(id) ---")
    query_max_id = "SELECT MAX(id) FROM logs"
    results_max_id = pnql_engine.execute_query(query_max_id)
    print(json.dumps(results_max_id, indent=2))
