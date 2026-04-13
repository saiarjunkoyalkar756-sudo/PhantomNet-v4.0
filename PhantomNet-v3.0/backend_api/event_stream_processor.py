# backend_api/event_stream_processor.py
import asyncio
import time
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from loguru import logger # Import loguru logger

# Assuming a basic event model
class RawEvent(BaseModel):
    id: str = Field(..., description="Unique event ID")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of the event")
    source: str = Field(..., description="Source of the event (e.g., 'BlueTeamAI', 'SensorX')")
    type: str = Field(..., description="Type of event (e.g., 'traffic_anomaly', 'login_attempt')")
    data: Dict[str, Any] = Field({}, description="Raw event data")

class CorrelatedEvent(RawEvent):
    correlation_id: str = Field(..., description="ID linking correlated events")
    related_events: List[str] = Field([], description="List of IDs of related events")
    severity: str = Field(..., description="Overall severity of the correlated event")
    ai_score: float = Field(..., ge=0, le=1.0, description="AI-driven correlation score")
    action_recommendation: Optional[str] = Field(None, description="Recommended action from AI")


class EventStreamProcessor:
    def __init__(self, websocket_broadcaster: callable, plugin_manager):
        self.websocket_broadcaster = websocket_broadcaster
        self.plugin_manager = plugin_manager
        self.raw_event_queue = asyncio.Queue()
        self.correlated_event_queue = asyncio.Queue()
        self.ai_correlation_plugin_name = "AI Anomaly Detector" # Using the AI anomaly detector as a correlation engine example
        self.loaded_ai_correlation = False

        # Try to load AI correlation plugin
        if self.plugin_manager.available_plugins.get(self.ai_correlation_plugin_name):
            self.loaded_ai_correlation = self.plugin_manager.load_plugin(self.ai_correlation_plugin_name)
            if not self.loaded_ai_correlation:
                logger.warning(f"Could not load AI correlation plugin '{self.ai_correlation_plugin_name}'. AI correlation will be simulated.")
        else:
            logger.warning(f"AI correlation plugin '{self.ai_correlation_plugin_name}' not found. AI correlation will be simulated.")


    async def ingest_event(self, event: RawEvent):
        """Ingests a raw event into the processing pipeline."""
        logger.info(f"[EventStream] Ingesting event: {event.id} from {event.source}")
        await self.raw_event_queue.put(event)

    async def _process_raw_events(self):
        """Processes raw events, performing basic aggregation and pushing for correlation."""
        while True:
            event = await self.raw_event_queue.get()
            logger.debug(f"[EventStream] Processing raw event {event.id}")
            
            # Simulate aggregation - for demo, just push to correlation queue
            # In a real system: group similar events, debounce, etc.
            await self.correlated_event_queue.put(event)
            self.raw_event_queue.task_done()

    async def _correlate_events_with_ai(self):
        """Correlates events using an AI plugin or simulation."""
        while True:
            event_to_correlate = await self.correlated_event_queue.get()
            logger.debug(f"[EventStream] Correlating event {event_to_correlate.id} with AI")

            correlated_event_data = await self._run_ai_correlation(event_to_correlate)
            
            # Simulate real-time alerts with priority scoring
            if correlated_event_data.get("is_anomaly", False) or correlated_event_data.get("ai_score", 0) > 0.7:
                severity_map = {0.0: "low", 0.5: "medium", 0.7: "high", 0.9: "critical"}
                current_severity = next((s for score, s in sorted(severity_map.items()) if correlated_event_data.get("ai_score", 0) >= score), "low")

                correlated_event = CorrelatedEvent(
                    id=event_to_correlate.id,
                    timestamp=event_to_correlate.timestamp,
                    source=event_to_correlate.source,
                    type=event_to_correlate.type,
                    data=event_to_correlate.data,
                    correlation_id=str(uuid.uuid4()),
                    related_events=[event_to_correlate.id],
                    severity=current_severity,
                    ai_score=correlated_event_data.get("ai_score", 0.0),
                    action_recommendation=correlated_event_data.get("suggested_action")
                )
                logger.warning(f"[EventStream] Real-time Alert (Severity: {correlated_event.severity}, Score: {correlated_event.ai_score:.2f}) for event {correlated_event.id}")
                await self.websocket_broadcaster({"type": "correlated_alert", "alert": correlated_event.dict()})
            else:
                logger.info(f"[EventStream] Event {event_to_correlate.id} processed, no high correlation detected.")
                # Still broadcast to dashboards for live updates if not an alert
                await self.websocket_broadcaster({"type": "processed_event", "event": event_to_correlate.dict()})

            self.correlated_event_queue.task_done()

    async def _run_ai_correlation(self, event_data: RawEvent) -> Dict[str, Any]:
        """Runs the AI correlation plugin or simulates its output."""
        if self.loaded_ai_correlation:
            try:
                # Call the sandboxed AI analysis plugin
                result = self.plugin_manager.execute_plugin_function(
                    self.ai_correlation_plugin_name, 
                    "analyze_event_for_anomaly", # Assuming this function exists in the AI plugin
                    event_data.dict() # Pass event data as dict
                )
                if result and not result.get("error"):
                    return result
                else:
                    logger.error(f"Error calling AI correlation plugin: {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"Exception during AI correlation plugin call: {e}")
        
        # Fallback to simple simulation if plugin is not loaded or fails
        is_anomaly = random.random() < 0.2 # 20% chance of anomaly
        ai_score = random.uniform(0.0, 1.0) if is_anomaly else random.uniform(0.0, 0.4)
        suggested_action = "Simulated Investigate" if is_anomaly else "Simulated Monitor"
        return {
            "is_anomaly": is_anomaly,
            "ai_score": ai_score,
            "suggested_action": suggested_action
        }

    async def start(self):
        """Starts the event processing and correlation pipelines."""
        logger.info("[EventStream] Starting event stream processor...")
        asyncio.create_task(self._process_raw_events())
        asyncio.create_task(self._correlate_events_with_ai())
        logger.info("[EventStream] Event stream processor started.")

# Example Usage (for testing)
if __name__ == "__main__":
    # Mock WebSocket Broadcaster
    async def mock_broadcast(event_json: Dict[str, Any]):
        print(f"MOCK BROADCAST: {json.dumps(event_json)}")

    # Mock PluginManager (needs to be able to load and execute anomaly detector)
    class MockPluginManager:
        def __init__(self):
            self.available_plugins = {
                "Anomaly Detector AI": {
                    "manifest": {
                        "name": "Anomaly Detector AI",
                        "entry_point": "anomaly_entry.py", # This would be used by SandboxRunner
                        "type": "ai_module",
                        "permissions": [],
                        "sandbox_config": {}
                    },
                    "path": "plugins/anomaly_detector_ai",
                    "status": "available"
                }
            }
            # For this mock, we don't need a real SandboxRunner, we'll simulate directly
        
        def load_plugin(self, plugin_name):
            if plugin_name in self.available_plugins:
                self.available_plugins[plugin_name]["status"] = "loaded"
                return True
            return False

        def execute_plugin_function(self, plugin_name: str, function_name: str, *args, **kwargs) -> Dict[str, Any]:
            if plugin_name == "Anomaly Detector AI" and function_name == "analyze_event_for_anomaly":
                event_data = args[0]
                is_anomaly = random.random() < 0.3 # Simulate 30% chance of anomaly
                ai_score = random.uniform(0.0, 1.0) if is_anomaly else random.uniform(0.0, 0.4)
                suggested_action = "MOCK Investigate" if is_anomaly else "MOCK Monitor"
                return {
                    "event_id": event_data.get("id", "N/A"),
                    "timestamp": time.time(),
                    "anomaly_score": round(ai_score, 3),
                    "is_anomaly": is_anomaly,
                    "prediction_confidence": round(random.uniform(0.6, 0.95), 3),
                    "suggested_action": suggested_action,
                    "simulated_by_mock_plugin": True
                }
            return {"error": "Mock plugin function not found."}


    mock_plugin_manager = MockPluginManager()
    processor = EventStreamProcessor(websocket_broadcaster=mock_broadcast, plugin_manager=mock_plugin_manager)

    async def test_stream():
        await processor.start()
        for i in range(10):
            event = RawEvent(id=f"TEST-EVENT-{i}", source="MockSource", type="network_packet", data={"payload_len": random.randint(50, 1000)})
            await processor.ingest_event(event)
            await asyncio.sleep(0.5) # Simulate event arrival
        
        # Give some time for events to be processed
        await asyncio.sleep(5)
        print("\n--- Test Stream Finished ---")

    asyncio.run(test_stream())
