import httpx
import logging
import json

logger = logging.getLogger(__name__)

# Base URLs for other microservices (these would typically come from configuration)
SERVICE_URLS = {
    "logs": "http://event_stream_processor:8000",  # Assumed endpoint for logs
    "assets": "http://asset_inventory:8000",
    "threat_intelligence": "http://threat_intelligence:8000",
    "mitre_attack": "http://mitre_attack_mapper:8000",
    "soar": "http://soar_engine:8000",
    # ... add other services as needed
}


def _build_query_params(condition: dict) -> dict:
    """
    Recursively traverses a condition tree and builds query parameters.
    This is a simplified example.
    """
    if "operator" in condition:
        op = condition["operator"]
        if op in ["=", "CONTAINS"]:
            return {f"{condition['field']}__{op.lower()}": condition["value"]}
        elif op in ["AND", "OR"]:
            left = _build_query_params(condition["left"])
            right = _build_query_params(condition["right"])
            # This is a naive merge. A real implementation needs to handle
            # key collisions and more complex logic.
            return {**left, **right}
    return {}


async def execute_query(parsed_query: dict) -> dict:
    """
    Executes a parsed PNQL query against relevant backend services.
    """
    command = parsed_query.get("command")
    service = parsed_query.get("service")
    target = parsed_query.get("target")

    results = {"message": f"Executing {command} command..."}

    async with httpx.AsyncClient() as client:
        if command == "SELECT":
            if service == "logs":
                # Example: SELECT * FROM logs WHERE severity = "HIGH"
                # This would translate to a call to the event_stream_processor's API
                logger.info(f"Querying logs from {SERVICE_URLS.get('logs')}/logs")

                # Extract WHERE clause and convert to query params
                params = {}
                if "condition" in parsed_query:
                    params = _build_query_params(parsed_query["condition"])

                try:
                    response = await client.get(
                        f"{SERVICE_URLS.get('logs')}/logs", params=params
                    )
                    response.raise_for_status()
                    results = response.json()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Error querying logs: {e}")
                    results = {"error": f"Error querying logs: {e.response.text}"}
            elif service == "assets":
                logger.info(f"Querying assets from {SERVICE_URLS.get('assets')}/assets")
                try:
                    response = await client.get(f"{SERVICE_URLS.get('assets')}/assets")
                    response.raise_for_status()
                    results = response.json()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Error querying assets: {e}")
                    results = {"error": f"Error querying assets: {e.response.text}"}
            # Add more service-specific SELECT logic here
            else:
                results = {
                    "error": f"SELECT command not supported for service: {service}"
                }

        elif command == "SCAN":
            # Example: SCAN "192.168.1.0/24" USING nmap WITH port="80,443"
            scan_target = parsed_query.get("target")
            scan_tools = parsed_query.get("tools")
            scan_options = parsed_query.get("options")
            logger.info(
                f"Initiating scan on {scan_target} using {scan_tools} with options {scan_options}"
            )

            if "nmap" in scan_tools and service == "assets":
                try:
                    # Assuming asset_inventory service has a /scan endpoint
                    response = await client.post(
                        f"{SERVICE_URLS.get('assets')}/scan",
                        json={"target": scan_target, "parameters": scan_options},
                    )
                    response.raise_for_status()
                    results = response.json()
                except httpx.HTTPStatusError as e:
                    logger.error(f"Error initiating scan: {e}")
                    results = {"error": f"Error initiating scan: {e.response.text}"}
            else:
                results = {
                    "error": f"SCAN command not supported for tools/service combination: {scan_tools}/{service}"
                }

        elif command == "SHOW":
            results = {"message": f"SHOW command placeholder for target {target}."}

        else:
            results = {"error": f"Unknown PNQL command: {command}"}

    return results


if __name__ == "__main__":
    # This block would typically not run in a microservice setup,
    # but for local testing, you could mock the httpx calls.
    # Example usage:
    # import asyncio
    # parsed = {"command": "SELECT", "type": "all", "service": "logs"}
    # asyncio.run(execute_query(parsed))
    pass
