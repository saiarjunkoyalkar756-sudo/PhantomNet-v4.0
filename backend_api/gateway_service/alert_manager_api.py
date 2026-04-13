from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from typing import List, Dict, Any, Optional
from loguru import logger
import asyncio
import json
from kafka import KafkaConsumer, KafkaProducer
import concurrent.futures

from .schemas import CorrelatedEvent # Assuming CorrelatedEvent is the schema for alerts
# Removed MockKafkaConsumer import

router = APIRouter()

# In-memory store for active alerts (mock for demonstration)
# In a real system, these would be fetched from the Threat/Alerts DB (e.g., Elasticsearch/MongoDB)
active_alerts_store: List[CorrelatedEvent] = []

# In-memory store for agent statuses (mock for demonstration)
# Key: agent_id, Value: last known status dict
agent_status_store: Dict[str, Dict[str, Any]] = {}

# WebSocket connections for real-time alerts
websocket_connections: List[WebSocket] = []

# WebSocket connections for real-time agent status
agent_status_websocket_connections: List[WebSocket] = []

# Kafka consumer for agent status updates
agent_status_kafka_consumer: Optional[KafkaConsumer] = None
agent_status_kafka_producer: Optional[KafkaProducer] = None
agent_status_producer_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None

AGENT_STATUS_TOPIC = "phantomnet.agent_status"
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092" # Make configurable later


@router.on_event("startup")
async def startup_event():
    global agent_status_kafka_consumer, agent_status_kafka_producer, agent_status_producer_executor
    logger.info("Alert Manager API starting up...")
    
    # Initialize Kafka consumer for agent status updates
    agent_status_kafka_consumer = KafkaConsumer(
        AGENT_STATUS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='alert-manager-agent-status-group'
    )
    logger.info("Alert Manager Kafka consumer initialized.")
    
    # Initialize Kafka producer for potential outbound messages (e.g., alerts to other topics)
    agent_status_kafka_producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','))
    agent_status_producer_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    logger.info("Alert Manager Kafka producer initialized.")

    asyncio.create_task(consume_agent_status_updates())
    logger.info("Started background task for consuming agent status updates.")


@router.get("/alerts/active", response_model=List[CorrelatedEvent])
async def get_active_alerts(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of items to return"),
    severity: Optional[str] = Query(None, description="Filter by severity (e.g., 'critical', 'high')"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    sort_by: str = Query("timestamp", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order ('asc' or 'desc')"),
):
    """
    Retrieves a list of currently active alerts with pagination, filtering, and sorting.
    """
    filtered_alerts = active_alerts_store

    if severity:
        filtered_alerts = [alert for alert in filtered_alerts if alert.severity.lower() == severity.lower()]
    
    if alert_type:
        filtered_alerts = [alert for alert in filtered_alerts if alert.type.lower() == alert_type.lower()]

    # Apply sorting
    if sort_by:
        reverse_sort = sort_order.lower() == "desc"
        try:
            # Need to handle different types for sorting
            if sort_by == "timestamp":
                filtered_alerts.sort(key=lambda alert: alert.timestamp, reverse=reverse_sort)
            elif sort_by == "severity":
                # Custom sort order for severity
                severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
                filtered_alerts.sort(key=lambda alert: severity_order.get(alert.severity.lower(), 0), reverse=reverse_sort)
            else:
                filtered_alerts.sort(key=lambda alert: getattr(alert, sort_by, ""), reverse=reverse_sort)
        except AttributeError:
            logger.warning(f"Sort by field '{sort_by}' not found or not sortable.")
        except Exception as e:
            logger.error(f"Error during sorting: {e}")

    # Apply pagination
    paginated_alerts = filtered_alerts[skip : skip + limit]

    logger.info(f"Retrieving {len(paginated_alerts)} active alerts (total: {len(filtered_alerts)}).")
    return paginated_alerts

@router.get("/alerts/{alert_id}", response_model=CorrelatedEvent)
async def get_alert_details(alert_id: str):
    """
    Retrieves the full details of a specific alert by its ID.
    """
    # In a real system, this would query the Threat/Alerts DB for the specific alert
    for alert in active_alerts_store:
        if alert.id == alert_id:
            return alert
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")


@router.websocket("/ws/alerts")
async def websocket_alert_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates on active alerts.
    """
    await websocket.accept()
    websocket_connections.append(websocket)
    logger.info("New WebSocket connection established for alert updates.")
    try:
        while True:
            # Keep the connection alive, or handle incoming messages (e.g., filter requests)
            await websocket.receive_text() # Expecting no specific incoming messages for now
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
        logger.info("WebSocket connection disconnected for alert updates.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_connections.remove(websocket)

async def broadcast_alert_update(alert: CorrelatedEvent):
    """
    Broadcasts a new or updated alert to all connected WebSocket clients.
    """
    message = json.dumps({"type": "alert_update", "alert": alert.dict()})
    for connection in websocket_connections:
        try:
            await connection.send_text(message)
        except WebSocketDisconnect:
            # Client disconnected, will be removed by websocket_alert_updates handler
            pass
        except Exception as e:
            logger.error(f"Error broadcasting to WebSocket client: {e}")

@router.post("/alerts/simulate", status_code=status.HTTP_201_CREATED)
async def simulate_alert(alert: CorrelatedEvent):
    """
    Simulates a new alert being generated and adds it to the active store.
    Also broadcasts the alert to WebSocket clients.
    """
    active_alerts_store.append(alert)
    await broadcast_alert_update(alert)
    logger.info(f"Simulated alert '{alert.id}' added and broadcasted.")
    return {"message": "Alert simulated and broadcasted."}


# --- Agent Status Update Section ---

@router.websocket("/ws/agent-status")
async def websocket_agent_status_updates(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates on agent statuses.
    """
    await websocket.accept()
    agent_status_websocket_connections.append(websocket)
    logger.info("New WebSocket connection established for agent status updates.")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        agent_status_websocket_connections.remove(websocket)
        logger.info("WebSocket connection disconnected for agent status updates.")
    except Exception as e:
        logger.error(f"Agent status WebSocket error: {e}")
        agent_status_websocket_connections.remove(websocket)


async def broadcast_agent_status_update(status_data: Dict[str, Any]):
    """
    Broadcasts a new agent status update to all connected WebSocket clients.
    """
    message = json.dumps({"type": "agent_status_update", "status": status_data})
    for connection in agent_status_websocket_connections:
        try:
            await connection.send_text(message)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Error broadcasting agent status to WebSocket client: {e}")


async def consume_agent_status_updates():
    """
    Consumes agent status updates from Kafka and broadcasts them via WebSocket.
    """
    if not agent_status_kafka_consumer:
        logger.error("Agent status Kafka consumer not initialized.")
        return

    logger.info(f"Starting Kafka consumer for agent status topic '{AGENT_STATUS_TOPIC}'...")
    loop = asyncio.get_running_loop()
    while True:
        messages = await loop.run_in_executor(None, agent_status_kafka_consumer.poll, 1000) # Poll for 1 second
        if messages is None:
            await asyncio.sleep(0.1) # Prevent busy-waiting
            continue
        for topic_partition, message_list in messages.items():
            for message in message_list:
                try:
                    if message.value is None:
                        logger.warning("Received None message value from Kafka.")
                        continue

                    status_data = json.loads(message.value.decode('utf-8'))
                    agent_id = status_data.get("agent_id")
                    if agent_id:
                        agent_status_store[str(agent_id)] = status_data # Store last known status
                        await broadcast_agent_status_update(status_data)
                        logger.debug(f"Consumed and broadcasted agent {agent_id} status update.")
                    else:
                        logger.warning(f"Received agent status update without agent_id: {status_data}")
                except json.JSONDecodeError as e:
                    logger.error(f"Agent status consumer: Failed to decode message as JSON: {e}, Message: {message.value[:200]}...")
                except Exception as e:
                    logger.error(f"Agent status consumer: Unexpected error processing message: {e}, Message: {message.value[:200]}...")
        await asyncio.sleep(0.1) # Small delay to prevent busy-waiting