import pika
import time
import logging
import json
import yaml
import re # Import re for condition evaluation
import httpx # Import httpx for making HTTP requests
from typing import Dict, Any, Optional

from .models import PlaybookStep, Playbook, PlaybookRun, PlaybookExecutionLog, PlaybookStatus # Import PlaybookStep and Playbook
from .state import playbooks_store, playbook_runs # Import playbooks_store and playbook_runs

logger = logging.getLogger(__name__)

# --- Placeholder Actions ---
# In a real implementation, these would interact with other systems
# (e.g., EDR agents, firewalls, ticketing systems)


def isolate_host(hostname: str, **kwargs):
    logger.info(f"[SOAR ACTION][EDR] Isolating host: {hostname}")
    return {"status": "success", "detail": f"Host {hostname} isolated via EDR."}


def block_ip(ip_address: str, **kwargs):
    logger.info(f"[SOAR ACTION][Firewall] Blocking IP: {ip_address}")
    return {"status": "success", "detail": f"IP {ip_address} blocked on firewall."}


def terminate_process(hostname: str, process_name: str, **kwargs):
    logger.info(
        f"[SOAR ACTION][EDR] Terminating process '{process_name}' on host: {hostname}"
    )
    return {
        "status": "success",
        "detail": f"Process {process_name} terminated on {hostname} via EDR.",
    }


def notify_soc(message: str, **kwargs):
    logger.info(f"[SOAR ACTION][Notification] Notifying SOC: {message}")
    # This could send an email, create a Jira ticket, post to Slack, etc.
    return {"status": "success", "detail": "SOC has been notified."}

def create_ticket(title: str, description: str, priority: str, **kwargs):
    logger.info(f"[SOAR ACTION][ITSM] Creating ticket: '{title}' with priority '{priority}'")
    # Simulate interaction with an ITSM tool
    ticket_id = f"INC-{int(time.time())}"
    return {"status": "success", "detail": f"Ticket '{ticket_id}' created in ITSM.", "ticket_id": ticket_id}

async def dispatch_agent_command(agent_id: str, command_type: str, payload: Dict[str, Any], **kwargs):
    """
    Dispatches a command to an agent via the Orchestrator's /commands/dispatch endpoint.
    """
    orchestrator_api_url = os.getenv("ORCHESTRATOR_API_URL", "http://localhost:8000/orchestrator") # Assuming API Gateway routes /orchestrator
    dispatch_url = f"{orchestrator_api_url}/commands/dispatch"
    
    logger.info(f"[SOAR ACTION][CommandDispatch] Dispatching command '{command_type}' to agent {agent_id}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                dispatch_url,
                json={
                    "agent_id": agent_id,
                    "command_type": command_type,
                    "payload": payload,
                    "initiated_by": "PN_SOAR_Engine"
                },
                timeout=5.0
            )
            response.raise_for_status()
            response_json = response.json()
            logger.info(f"[SOAR ACTION][CommandDispatch] Command dispatch successful: {response_json}")
            return {"status": "success", "detail": response_json.get("message", "Command dispatched"), "command_id": response_json.get("command_id")}
    except httpx.HTTPStatusError as e:
        logger.error(f"[SOAR ACTION][CommandDispatch] Failed to dispatch command - HTTP Error: {e.response.status_code} {e.response.text}")
        return {"status": "failure", "detail": f"HTTP Error: {e.response.status_code} {e.response.text}"}
    except httpx.RequestError as e:
        logger.error(f"[SOAR ACTION][CommandDispatch] Failed to dispatch command - Network Error: {e}")
        return {"status": "failure", "detail": f"Network Error: {e}"}
    except Exception as e:
        logger.error(f"[SOAR ACTION][CommandDispatch] Unexpected error during command dispatch: {e}")
        return {"status": "failure", "detail": f"Unexpected error: {e}"}


# Centralized map for actions, potentially organized by tool
# This allows for more flexible dispatch based on tool_name in PlaybookStep
ACTION_MAP = {
    "isolate_host": isolate_host,
    "block_ip": block_ip,
    "terminate_process": terminate_process,
    "notify_soc": notify_soc,
    "create_ticket": create_ticket, # New action for ITSM tool integration
    "dispatch_agent_command": dispatch_agent_command, # New action for agent command dispatch
}

# --- End Placeholder Actions ---


def render_template(template_string: str, context: Dict[str, Any]) -> str:
    """
    Simple template rendering to replace placeholders like {{ event.hostname }} or {{ context.incident_id }}.
    """
    if not isinstance(template_string, str):
        return template_string # Return as is if not a string (e.g., boolean, number)

    # Replace event-related placeholders
    for key, value in context.get("event", {}).items():
        template_string = template_string.replace(f"{{{{ event.{key} }}}}", str(value))
    
    # Replace context-related placeholders (e.g., from playbook.context or prior step results)
    for key, value in context.get("context", {}).items():
        template_string = template_string.replace(f"{{{{ context.{key} }}}}", str(value))

    return template_string

def _safe_evaluate_expression(expression: str, context_values: Dict[str, Any]) -> bool:
    """
    Safely evaluates a simple boolean expression against provided context values.
    Supports '==', '!=', '>', '>=', '<', '<=' for basic types, and 'and', 'or', 'not'.
    This is a minimalistic, secure replacement for eval().
    """
    # Replace context variable placeholders with their actual values
    # e.g., "event.severity" becomes "critical" or "context.value" becomes 10
    for key, value in context_values.items():
        # Ensure values are properly quoted if they are strings
        if isinstance(value, str):
            expression = expression.replace(key, f"'{value}'")
        else:
            expression = expression.replace(key, str(value))

    # Basic tokenization and evaluation for safety
    # This example only supports simple equality/inequality for illustration
    # A full safe expression parser would be more complex
    
    # Very basic example, more robust logic needed for full expression support
    # This is a placeholder for a true safe expression parsing library.
    # For demo stability, we'll try to parse basic comparison.
    
    # Example: "incident.severity == 'critical'"
    # Step 1: Split by '=='
    if '==' in expression:
        parts = [p.strip() for p in expression.split('==', 1)]
        if len(parts) == 2:
            return parts[0] == parts[1]
    if '!=' in expression:
        parts = [p.strip() for p in expression.split('!=', 1)]
        if len(parts) == 2:
            return parts[0] != parts[1]
    if '>=' in expression:
        parts = [p.strip() for p in expression.split('>=', 1)]
        if len(parts) == 2:
            try: return float(parts[0]) >= float(parts[1])
            except ValueError: pass
    if '<=' in expression:
        parts = [p.strip() for p in expression.split('<=', 1)]
        if len(parts) == 2:
            try: return float(parts[0]) <= float(parts[1])
            except ValueError: pass
    if '>' in expression:
        parts = [p.strip() for p in expression.split('>', 1)]
        if len(parts) == 2:
            try: return float(parts[0]) > float(parts[1])
            except ValueError: pass
    if '<' in expression:
        parts = [p.strip() for p in expression.split('<', 1)]
        if len(parts) == 2:
            try: return float(parts[0]) < float(parts[1])
            except ValueError: pass

    # Add more complex logic here for 'and', 'or', 'not' if necessary
    # For now, if it's not a simple comparison, we'll log a warning and return False
    logger.warning(f"SOAR: Complex condition '{expression}' not fully supported by safe evaluator. Returning False.")
    return False

def evaluate_condition(condition_str: Optional[str], context: Dict[str, Any]) -> bool:
    """
    Evaluates a simple condition string (e.g., "incident.severity == 'critical'")
    against the provided context.
    """
    if not condition_str:
        return True # No condition, so always true

    # Prepare context values for safe evaluation
    context_values = {}
    for key, value in context.get("event", {}).items():
        context_values[f"event.{key}"] = value
    for key, value in context.get("context", {}).items():
        context_values[f"context.{key}"] = value
    
    # --- Conceptual Integration with PN_Policy_Engine ---
    # In a real scenario, the condition evaluation could involve querying the PN_Policy_Engine
    # for dynamic policy decisions.
    # Example: If condition involves "policy:allow_high_risk_action"
    #   if "policy:allow_high_risk_action" in condition_str:
    #       # Make an API call to PN_Policy_Engine
    #       # policy_decision = await policy_engine.evaluate(request_context)
    #       # evaluated_condition = evaluated_condition.replace("policy:allow_high_risk_action", str(policy_decision.is_allowed))
    # This is a placeholder to show the integration point.
    # --- End Conceptual Integration ---

    try:
        # Use a safe evaluator instead of eval
        return _safe_evaluate_expression(condition_str, context_values)
    except Exception as e:
        logger.error(f"Error evaluating condition '{condition_str}': {e}.", exc_info=True)
        return False


def execute_playbook(playbook_run: PlaybookRun): # Modified to accept PlaybookRun directly
    logger.info(f"Executing playbook: {playbook_run.playbook_name} (Run ID: {playbook_run.run_id})")
    
    # Initialize execution context for adaptive playbooks
    # playbook_run.current_context is already initialized with triggered_by incident context
    # Add step_results to current_context
    playbook_run.current_context["step_results"] = {}

    for idx, step in enumerate(playbook_run.playbook.steps): # Iterate through playbook.steps from the playbook_run object
        step_status = PlaybookStatus.SKIPPED # Use Enum
        step_result_details: Dict[str, Any] = {} # To store raw results from action functions
        step_output: Dict[str, Any] = {} # To store formatted output for PlaybookExecutionLog

        # Evaluate step condition (adaptive playbook logic)
        if step.condition:
            # Use current_context for condition evaluation
            if not evaluate_condition(step.condition, {"event": playbook_run.triggered_by, "context": playbook_run.current_context}):
import time
import logging
import json
import yaml
import re # Import re for condition evaluation
import httpx # Import httpx for making HTTP requests
import os # Import os for environment variables
import asyncio # Import asyncio for async operations
from typing import Dict, Any, Optional

from kafka import KafkaConsumer, KafkaProducer # Import Kafka classes
from kafka.errors import NoBrokersAvailable # Import Kafka error
from kafka.admin import KafkaAdminClient, NewTopic # Import for checking topic existence

from .models import PlaybookStep, Playbook, PlaybookRun, PlaybookExecutionLog, PlaybookStatus # Import PlaybookStep and Playbook
from .state import playbooks_store, playbook_runs # Import playbooks_store and playbook_runs

logger = logging.getLogger(__name__)

# --- Kafka Configuration ---
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:29092')
SOAR_ALERT_TOPIC = os.getenv('SOAR_ALERT_TOPIC', 'soar-alerts')
GROUP_ID = os.getenv('SOAR_KAFKA_GROUP_ID', 'soar-engine-group')

# --- SAFE MODE Flags ---
KAFKA_SAFE_MODE = False
KAFKA_SAFE_MODE_REASON = ""

# --- Global Kafka Instances ---
soar_kafka_consumer: Optional[KafkaConsumer] = None
soar_kafka_producer: Optional[KafkaProducer] = None
stop_consuming_event = asyncio.Event()


# --- Placeholder Actions ---
# In a real implementation, these would interact with other systems
# (e.g., EDR agents, firewalls, ticketing systems)


def isolate_host(hostname: str, **kwargs):
    logger.info(f"[SOAR ACTION][EDR] Isolating host: {hostname}")
    return {"status": "success", "detail": f"Host {hostname} isolated via EDR."}


def block_ip(ip_address: str, **kwargs):
    logger.info(f"[SOAR ACTION][Firewall] Blocking IP: {ip_address}")
    return {"status": "success", "detail": f"IP {ip_address} blocked on firewall."}


def terminate_process(hostname: str, process_name: str, **kwargs):
    logger.info(
        f"[SOAR ACTION][EDR] Terminating process '{process_name}' on host: {hostname}"
    )
    return {
        "status": "success",
        "detail": f"Process {process_name} terminated on {hostname} via EDR.",
    }


def notify_soc(message: str, **kwargs):
    logger.info(f"[SOAR ACTION][Notification] Notifying SOC: {message}")
    # This could send an email, create a Jira ticket, post to Slack, etc.
    return {"status": "success", "detail": "SOC has been notified."}

def create_ticket(title: str, description: str, priority: str, **kwargs):
    logger.info(f"[SOAR ACTION][ITSM] Creating ticket: '{title}' with priority '{priority}'")
    # Simulate interaction with an ITSM tool
    ticket_id = f"INC-{int(time.time())}"
    return {"status": "success", "detail": f"Ticket '{ticket_id}' created in ITSM.", "ticket_id": ticket_id}

async def dispatch_agent_command(agent_id: str, command_type: str, payload: Dict[str, Any], **kwargs):
    """
    Dispatches a command to an agent via the Orchestrator's /commands/dispatch endpoint.
    """
    orchestrator_api_url = os.getenv("ORCHESTRATOR_API_URL", "http://localhost:8000/orchestrator") # Assuming API Gateway routes /orchestrator
    dispatch_url = f"{orchestrator_api_url}/commands/dispatch"
    
    logger.info(f"[SOAR ACTION][CommandDispatch] Dispatching command '{command_type}' to agent {agent_id}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                dispatch_url,
                json={
                    "agent_id": agent_id,
                    "command_type": command_type,
                    "payload": payload,
                    "initiated_by": "PN_SOAR_Engine"
                },
                timeout=5.0
            )
            response.raise_for_status()
            response_json = response.json()
            logger.info(f"[SOAR ACTION][CommandDispatch] Command dispatch successful: {response_json}")
            return {"status": "success", "detail": response_json.get("message", "Command dispatched"), "command_id": response_json.get("command_id")}
    except httpx.HTTPStatusError as e:
        logger.error(f"[SOAR ACTION][CommandDispatch] Failed to dispatch command - HTTP Error: {e.response.status_code} {e.response.text}")
        return {"status": "failure", "detail": f"HTTP Error: {e.response.status_code} {e.response.text}"}
    except httpx.RequestError as e:
        logger.error(f"[SOAR ACTION][CommandDispatch] Failed to dispatch command - Network Error: {e}")
        return {"status": "failure", "detail": f"Network Error: {e}"}
    except Exception as e:
        logger.error(f"[SOAR ACTION][CommandDispatch] Unexpected error during command dispatch: {e}")
        return {"status": "failure", "detail": f"Unexpected error: {e}"}


# Centralized map for actions, potentially organized by tool
# This allows for more flexible dispatch based on tool_name in PlaybookStep
ACTION_MAP = {
    "isolate_host": isolate_host,
    "block_ip": block_ip,
    "terminate_process": terminate_process,
    "notify_soc": notify_soc,
    "create_ticket": create_ticket, # New action for ITSM tool integration
    "dispatch_agent_command": dispatch_agent_command, # New action for agent command dispatch
}

# --- End Placeholder Actions ---


def render_template(template_string: str, context: Dict[str, Any]) -> str:
    """
    Simple template rendering to replace placeholders like {{ event.hostname }} or {{ context.incident_id }}.
    """
    if not isinstance(template_string, str):
        return template_string # Return as is if not a string (e.g., boolean, number)

    # Replace event-related placeholders
    for key, value in context.get("event", {}).items():
        template_string = template_string.replace(f"{{{{ event.{key} }}}}", str(value))
    
    # Replace context-related placeholders (e.g., from playbook.context or prior step results)
    for key, value in context.get("context", {}).items():
        template_string = template_string.replace(f"{{{{ context.{key} }}}}", str(value))

    return template_string

def _safe_evaluate_expression(expression: str, context_values: Dict[str, Any]) -> bool:
    """
    Safely evaluates a simple boolean expression against provided context values.
    Supports '==', '!=', '>', '>=', '<', '<=' for basic types, and 'and', 'or', 'not'.
    This is a minimalistic, secure replacement for eval().
    """
    # Replace context variable placeholders with their actual values
    # e.g., "event.severity" becomes "critical" or "context.value" becomes 10
    for key, value in context_values.items():
        # Ensure values are properly quoted if they are strings
        if isinstance(value, str):
            expression = expression.replace(key, f"'{value}'")
        else:
            expression = expression.replace(key, str(value))

    # Basic tokenization and evaluation for safety
    # This example only supports simple equality/inequality for illustration
    # A full safe expression parser would be more complex
    
    # Very basic example, more robust logic needed for full expression support
    # This is a placeholder for a true safe expression parsing library.
    # For demo stability, we'll try to parse basic comparison.
    
    # Example: "incident.severity == 'critical'"
    # Step 1: Split by '=='
    if '==' in expression:
        parts = [p.strip() for p in expression.split('==', 1)]
        if len(parts) == 2:
            return parts[0] == parts[1]
    if '!=' in expression:
        parts = [p.strip() for p in expression.split('!=', 1)]
        if len(parts) == 2:
            return parts[0] != parts[1]
    if '>=' in expression:
        parts = [p.strip() for p in expression.split('>=', 1)]
        if len(parts) == 2:
            try: return float(parts[0]) >= float(parts[1])
            except ValueError: pass
    if '<=' in expression:
        parts = [p.strip() for p in expression.split('<=', 1)]
        if len(parts) == 2:
            try: return float(parts[0]) <= float(parts[1])
            except ValueError: pass
    if '>' in expression:
        parts = [p.strip() for p in expression.split('>', 1)]
        if len(parts) == 2:
            try: return float(parts[0]) > float(parts[1])
            except ValueError: pass
    if '<' in expression:
        parts = [p.strip() for p in expression.split('<', 1)]
        if len(parts) == 2:
            try: return float(parts[0]) < float(parts[1])
            except ValueError: pass

    # Add more complex logic here for 'and', 'or', 'not' if necessary
    # For now, if it's not a simple comparison, we'll log a warning and return False
    logger.warning(f"SOAR: Complex condition '{expression}' not fully supported by safe evaluator. Returning False.")
    return False

def evaluate_condition(condition_str: Optional[str], context: Dict[str, Any]) -> bool:
    """
    Evaluates a simple condition string (e.g., "incident.severity == 'critical'")
    against the provided context.
    """
    if not condition_str:
        return True # No condition, so always true

    # Prepare context values for safe evaluation
    context_values = {}
    for key, value in context.get("event", {}).items():
        context_values[f"event.{key}"] = value
    for key, value in context.get("context", {}).items():
        context_values[f"context.{key}"] = value
    
    # --- Conceptual Integration with PN_Policy_Engine ---
    # In a real scenario, the condition evaluation could involve querying the PN_Policy_Engine
    # for dynamic policy decisions.
    # Example: If condition involves "policy:allow_high_risk_action"
    #   if "policy:allow_high_risk_action" in condition_str:
    #       # Make an API call to PN_Policy_Engine
    #       # policy_decision = await policy_engine.evaluate(request_context)
    #       # evaluated_condition = evaluated_condition.replace("policy:allow_high_risk_action", str(policy_decision.is_allowed))
    # This is a placeholder to show the integration point.
    # --- End Conceptual Integration ---

    try:
        # Use a safe evaluator instead of eval
        return _safe_evaluate_expression(condition_str, context_values)
    except Exception as e:
        logger.error(f"Error evaluating condition '{condition_str}': {e}.", exc_info=True)
        return False


def execute_playbook(playbook_run: PlaybookRun): # Modified to accept PlaybookRun directly
    logger.info(f"Executing playbook: {playbook_run.playbook_name} (Run ID: {playbook_run.run_id})")
    
    # Initialize execution context for adaptive playbooks
    # playbook_run.current_context is already initialized with triggered_by incident context
    # Add step_results to current_context
    playbook_run.current_context["step_results"] = {}

    for idx, step in enumerate(playbook_run.playbook.steps): # Iterate through playbook.steps from the playbook_run object
        step_status = PlaybookStatus.SKIPPED # Use Enum
        step_result_details: Dict[str, Any] = {} # To store raw results from action functions
        step_output: Dict[str, Any] = {} # To store formatted output for PlaybookExecutionLog

        # Evaluate step condition (adaptive playbook logic)
        if step.condition:
            # Use current_context for condition evaluation
            if not evaluate_condition(step.condition, {"event": playbook_run.triggered_by, "context": playbook_run.current_context}):
                logger.info(f"Step {idx+1} '{step.action}' skipped due to condition: '{step.condition}'")
                
                playbook_run.execution_logs.append(
                    PlaybookExecutionLog(
                        step_action=step.action,
                        status=PlaybookStatus.SKIPPED,
                        details="Condition not met.",
                        output=step_output
                    )
                )
                continue # Skip to next step

        action_name = step.action
        action_func = ACTION_MAP.get(action_name)

        if not action_func:
            logger.error(f"Action '{action_name}' not found in ACTION_MAP.")
            step_status = PlaybookStatus.FAILED # Use Enum
            step_result_details = {"status": "failure", "detail": f"Action '{action_name}' not implemented or found."}
        else:
            # Prepare parameters, rendering templates using current execution context
            rendered_params = {}
            for param_name, param_value in step.parameters.items():
                rendered_params[param_name] = render_template(str(param_value), {"event": playbook_run.triggered_by, "context": playbook_run.current_context})
            
            try:
                # Execute action
                logger.info(f"Executing step {idx+1}: Tool='{step.tool_name}', Action='{action_name}' with params: {rendered_params}")
                
                # NOTE: Assuming action_func is synchronous here. If it can be async,
                # this consumer's execute_playbook would need to be async and called
                # via an event loop (e.g., asyncio.run or asyncio.create_task)
                step_result_details = action_func(**rendered_params) # Call sync actions
                
                step_status = PlaybookStatus.COMPLETED if step_result_details.get("status") == "success" else PlaybookStatus.FAILED # Use Enum
                
                # Store step result in context for subsequent steps (adaptive playbook logic)
                if step.output_to:
                    playbook_run.current_context["step_results"][step.output_to] = step_result_details
                else:
                    playbook_run.current_context["step_results"][action_name] = step_result_details


            except Exception as e:
                logger.error(
                    f"Error executing step '{action_name}': {e}", exc_info=True
                )
                step_status = PlaybookStatus.FAILED # Use Enum
                step_result_details = {"status": "failure", "detail": str(e)}

        playbook_run.execution_logs.append(
            PlaybookExecutionLog(
                step_action=step.action,
                status=step_status,
                details=step_result_details.get("detail", ""),
                output=step_result_details # Store full details as output
            )
        )
        
        if step_status == PlaybookStatus.FAILED: # Use Enum
            playbook_run.status = PlaybookStatus.FAILED # Use Enum
            playbook_run.end_time = datetime.utcnow()
            logger.error(f"Playbook '{playbook_run.playbook_name}' failed at step '{step.action}'.")
            break # Stop playbook execution on failure

    if playbook_run.status == PlaybookStatus.PENDING: # Only if not already failed by a step
        playbook_run.status = PlaybookStatus.COMPLETED # Use Enum
    
    playbook_run.end_time = datetime.utcnow()
    # The playbook_run object is already in playbook_runs, so no need to re-add.
    logger.info(f"Playbook '{playbook_run.playbook_name}' execution finished with status: {playbook_run.status}.")


async def initialize_kafka_consumer():
    """Initializes and returns the Kafka consumer."""
    global KAFKA_SAFE_MODE, KAFKA_SAFE_MODE_REASON
    try:
        # Check if topic exists, create if not (for demo purposes)
        admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        existing_topics = admin_client.list_topics()
        if SOAR_ALERT_TOPIC not in existing_topics:
            logger.warning(f"Kafka topic '{SOAR_ALERT_TOPIC}' does not exist. Attempting to create.")
            new_topic = NewTopic(name=SOAR_ALERT_TOPIC, num_partitions=1, replication_factor=1)
            admin_client.create_topics(new_topics=[new_topic], validate_only=False)
            logger.info(f"Kafka topic '{SOAR_ALERT_TOPIC}' created.")
        admin_client.close()

        consumer = KafkaConsumer(
            SOAR_ALERT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=GROUP_ID,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        logger.info(f"Kafka consumer initialized for topic '{SOAR_ALERT_TOPIC}'.")
        KAFKA_SAFE_MODE = False
        return consumer
    except NoBrokersAvailable:
        KAFKA_SAFE_MODE = True
        KAFKA_SAFE_MODE_REASON = "Kafka: No brokers available."
        logger.error(KAFKA_SAFE_MODE_REASON)
        return None
    except Exception as e:
        KAFKA_SAFE_MODE = True
        KAFKA_SAFE_MODE_REASON = f"Kafka initialization error: {e}"
        logger.error(KAFKA_SAFE_MODE_REASON, exc_info=True)
        return None

async def process_kafka_message(message):
    """Processes a single Kafka message."""
    try:
        alert = message.value
        logger.info(f"SOAR Engine received alert from Kafka: {alert.get('alert_name')}")

        # Find and execute the corresponding playbook
        for playbook_name, playbook_obj in playbooks_store.items():
            if playbook_obj.trigger.get("alert_name") == alert.get("alert_name"):
                playbook_run = PlaybookRun(
                    playbook_name=playbook_obj.name,
                    triggered_by=alert,
                    playbook=playbook_obj,
                    current_context={"incident": alert}
                )
                playbook_runs[playbook_run.run_id] = playbook_run
                execute_playbook(playbook_run)
                break

    except json.JSONDecodeError:
        logger.error(f"Failed to decode Kafka message body as JSON: {message.value}")
    except Exception as e:
        logger.error(f"Error processing Kafka message: {e}", exc_info=True)

async def consume_kafka_messages():
    """Main loop for consuming Kafka messages."""
    global soar_kafka_consumer, KAFKA_SAFE_MODE, KAFKA_SAFE_MODE_REASON
    
    # Attempt to initialize consumer if not already done or in SAFE MODE
    if soar_kafka_consumer is None or KAFKA_SAFE_MODE:
        soar_kafka_consumer = await initialize_kafka_consumer()
        if soar_kafka_consumer is None:
            logger.error("Failed to initialize Kafka consumer. SOAR will not process alerts.")
            return

    try:
        while not stop_consuming_event.is_set():
            if KAFKA_SAFE_MODE:
                logger.warning("Kafka is in SAFE MODE. Retrying connection in 30 seconds.")
                await asyncio.sleep(30)
                soar_kafka_consumer = await initialize_kafka_consumer()
                if soar_kafka_consumer is None:
                    continue
            
            for message in soar_kafka_consumer:
                if stop_consuming_event.is_set():
                    break
                await process_kafka_message(message)
                # Allow other tasks to run
                await asyncio.sleep(0.01)

            # If consumer loop finishes (e.g., rebalance), re-initialize
            if not stop_consuming_event.is_set():
                logger.warning("Kafka consumer loop ended. Re-initializing consumer.")
                soar_kafka_consumer = await initialize_kafka_consumer()
                if soar_kafka_consumer is None:
                    await asyncio.sleep(5) # Wait before retry
                    
    except asyncio.CancelledError:
        logger.info("Kafka consumer task cancelled.")
    except Exception as e:
        logger.critical(f"Critical error in Kafka consumer loop: {e}", exc_info=True)
        KAFKA_SAFE_MODE = True # Assume Kafka is down
        KAFKA_SAFE_MODE_REASON = f"Critical consumer error: {e}"
        await asyncio.sleep(10) # Wait before retry
    finally:
        if soar_kafka_consumer:
            soar_kafka_consumer.close()
            logger.info("Kafka consumer closed.")


async def start_soar_consumer_task():
    """Starts the Kafka consumer task for SOAR alerts."""
    global soar_consumer_task
    soar_consumer_task = asyncio.create_task(consume_kafka_messages())
    logger.info("SOAR Kafka consumer task started.")

async def stop_soar_consumer_task():
    """Stops the Kafka consumer task."""
    global soar_consumer_task
    stop_consuming_event.set()
    if soar_consumer_task:
        soar_consumer_task.cancel()
        try:
            await soar_consumer_task
        except asyncio.CancelledError:
            logger.info("SOAR Kafka consumer task stopped.")
                
                playbook_run.execution_logs.append(
                    PlaybookExecutionLog(
                        step_action=step.action,
                        status=PlaybookStatus.SKIPPED,
                        details="Condition not met.",
                        output=step_output
                    )
                )
                continue # Skip to next step

        action_name = step.action
        action_func = ACTION_MAP.get(action_name)

        if not action_func:
            logger.error(f"Action '{action_name}' not found in ACTION_MAP.")
            step_status = PlaybookStatus.FAILED # Use Enum
            step_result_details = {"status": "failure", "detail": f"Action '{action_name}' not implemented or found."}
        else:
            # Prepare parameters, rendering templates using current execution context
            rendered_params = {}
            for param_name, param_value in step.parameters.items():
                rendered_params[param_name] = render_template(str(param_value), {"event": playbook_run.triggered_by, "context": playbook_run.current_context})
            
            try:
                # Execute action
                logger.info(f"Executing step {idx+1}: Tool='{step.tool_name}', Action='{action_name}' with params: {rendered_params}")
                
                # NOTE: Assuming action_func is synchronous here. If it can be async,
                # this consumer's execute_playbook would need to be async and called
                # via an event loop (e.g., asyncio.run or asyncio.create_task)
                step_result_details = action_func(**rendered_params) # Call sync actions
                
                step_status = PlaybookStatus.COMPLETED if step_result_details.get("status") == "success" else PlaybookStatus.FAILED # Use Enum
                
                # Store step result in context for subsequent steps (adaptive playbook logic)
                if step.output_to:
                    playbook_run.current_context["step_results"][step.output_to] = step_result_details
                else:
                    playbook_run.current_context["step_results"][action_name] = step_result_details


            except Exception as e:
                logger.error(
                    f"Error executing step '{action_name}': {e}", exc_info=True
                )
                step_status = PlaybookStatus.FAILED # Use Enum
                step_result_details = {"status": "failure", "detail": str(e)}

        playbook_run.execution_logs.append(
            PlaybookExecutionLog(
                step_action=step.action,
                status=step_status,
                details=step_result_details.get("detail", ""),
                output=step_result_details # Store full details as output
            )
        )
        
        if step_status == PlaybookStatus.FAILED: # Use Enum
            playbook_run.status = PlaybookStatus.FAILED # Use Enum
            playbook_run.end_time = datetime.utcnow()
            logger.error(f"Playbook '{playbook_run.playbook_name}' failed at step '{step.action}'.")
            break # Stop playbook execution on failure

    if playbook_run.status == PlaybookStatus.PENDING: # Only if not already failed by a step
        playbook_run.status = PlaybookStatus.COMPLETED # Use Enum
    
    playbook_run.end_time = datetime.utcnow()
    # The playbook_run object is already in playbook_runs, so no need to re-add.
    logger.info(f"Playbook '{playbook_run.playbook_name}' execution finished with status: {playbook_run.status}.")



