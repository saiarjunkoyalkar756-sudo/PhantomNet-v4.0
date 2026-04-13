# backend_api/blue_team_ai.py
import asyncio
import time
import random
from typing import Dict, Any
from backend_api.plugin_manager import PluginManager # Import PluginManager

class BlueTeamAI:
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.anomaly_detector_plugin_name = "Anomaly Detector AI"
        self.loaded_anomaly_detector = False
        
        # Ensure the anomaly detector plugin is loaded
        if self.plugin_manager.available_plugins.get(self.anomaly_detector_plugin_name):
            self.loaded_anomaly_detector = self.plugin_manager.load_plugin(self.anomaly_detector_plugin_name)
            if not self.loaded_anomaly_detector:
                print(f"Warning: Could not load Anomaly Detector AI plugin '{self.anomaly_detector_plugin_name}'. Anomaly detection will be simulated.")
        else:
            print(f"Warning: Anomaly Detector AI plugin '{self.anomaly_detector_plugin_name}' not found. Anomaly detection will be simulated.")


    async def _simulate_traffic_event(self) -> Dict[str, Any]:
        """Simulates capturing a single network traffic event."""
        event_id = str(random.randint(10000, 99999))
        source_ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
        destination_ip = f"10.0.{random.randint(1, 254)}.{random.randint(1, 254)}"
        port = random.choice([21, 22, 23, 80, 443, 445, 3389, 8080])
        protocol = random.choice(["TCP", "UDP", "ICMP"])
        packet_size = random.randint(64, 1500)
        
        # Simulate some event characteristics that might influence anomaly score
        severity = random.uniform(0.1, 0.9)
        frequency = random.uniform(0.01, 0.5)

        return {
            "id": event_id,
            "timestamp": time.time(),
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "port": port,
            "protocol": protocol,
            "packet_size": packet_size,
            "severity": severity,
            "frequency": frequency
        }

    async def monitor_traffic_stream(self, interval: int = 1) -> Dict[str, Any]:
        """
        Simulates real-time traffic monitoring and feeds data for anomaly detection.
        This is a generator that yields simulated traffic events.
        """
        while True:
            event = await self._simulate_traffic_event()
            print(f"[BlueTeamAI] Monitored traffic event: {event['id']}")
            yield event
            await asyncio.sleep(interval)

    async def analyze_traffic_for_anomalies(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a traffic event for anomalies using the loaded AI analysis plugin.
        """
        print(f"[BlueTeamAI] Analyzing event {event_data['id']} for anomalies...")
        if self.loaded_anomaly_detector:
            # Call the sandboxed AI analysis plugin
            result = self.plugin_manager.execute_plugin_function(
                self.anomaly_detector_plugin_name,
                "analyze_event_for_anomaly",
                event_data
            )
            if result and not result.get("error"):
                return result
            else:
                print(f"Error calling Anomaly Detector AI plugin: {result.get('error', 'Unknown error')}")
                # Fallback to simple simulation if plugin call fails
        
        # Simple simulation if plugin is not loaded or fails
        print("[BlueTeamAI] Simulating anomaly detection (plugin not available or failed).")
        is_anomaly = random.random() < 0.1 # 10% chance of anomaly
        anomaly_score = random.uniform(0.0, 1.0) if is_anomaly else random.uniform(0.0, 0.3)
        return {
            "event_id": event_data.get("id", "N/A"),
            "timestamp": time.time(),
            "anomaly_score": round(anomaly_score, 3),
            "is_anomaly": is_anomaly,
            "prediction_confidence": round(random.uniform(0.5, 0.9), 3),
            "suggested_action": "Simulated Investigate" if is_anomaly else "Simulated Monitor"
        }

    async def run_defense_cycle(self, interval: int = 5):
        """
        Runs a continuous cycle of monitoring, analysis, and defense actions.
        """
        print("[BlueTeamAI] Starting autonomous blue team defense cycle.")
        async for event in self.monitor_traffic_stream(interval):
            anomaly_analysis = await self.analyze_traffic_for_anomalies(event)
            print(f"[BlueTeamAI] Event {event['id']} - Anomaly Status: {anomaly_analysis['is_anomaly']}, Score: {anomaly_analysis['anomaly_score']}")
            
            if anomaly_analysis["is_anomaly"]:
                print(f"[BlueTeamAI] ANOMALY DETECTED! Suggested action: {anomaly_analysis['suggested_action']}")
                # Here would be calls to auto-block, patch configs, update firewall, isolate hosts etc.
                await self.take_defense_action(event, anomaly_analysis)
            else:
                print(f"[BlueTeamAI] Event {event['id']} - No anomaly detected.")
    
    async def take_defense_action(self, event: Dict[str, Any], anomaly_analysis: Dict[str, Any]):
        """
        Simulates taking a defense action based on the anomaly analysis.
        This would integrate with other PhantomNet modules (e.g., firewall, orchestrator).
        """
        action = anomaly_analysis.get("suggested_action", "Investigate")
        source_ip = event.get("source_ip", "unknown")

        print(f"[BlueTeamAI] Taking defense action: '{action}' against {source_ip} (simulated).")
        # In a real system, this would trigger actual defense mechanisms:
        # - call firewall API to block IP
        # - notify orchestrator to isolate host
        # - generate a more formal SOC alert
        print(f"[BlueTeamAI] SOC Alert generated for event {event['id']} from {source_ip}.")
        # Example of generating a SOC alert (could be sent via FastAPI endpoint)
        # await app.post("/alerts/soc", json={"type": "anomaly_detected", "event": event, "analysis": anomaly_analysis})
        
        await asyncio.sleep(random.uniform(0.5, 2.0)) # Simulate action time
        print(f"[BlueTeamAI] Defense action for {event['id']} completed (simulated).")

# Example Usage
if __name__ == "__main__":
    # This requires a running Docker daemon and the "Anomaly Detector AI" plugin to be present.
    # For testing this script directly, we need a dummy plugin manager.
    
    # Dummy PluginManager for standalone testing of BlueTeamAI
    class DummyPluginManager:
        def __init__(self):
            self.available_plugins = {
                "Anomaly Detector AI": {
                    "manifest": {
                        "name": "Anomaly Detector AI",
                        "entry_point": "anomaly_entry.py",
                        "type": "ai_module",
                        "permissions": [],
                        "sandbox_config": {}
                    },
                    "path": "plugins/anomaly_detector_ai",
                    "status": "available"
                }
            }
            self.sandbox_runner = PluginManager().sandbox_runner # Re-use actual sandbox runner for testing

        def load_plugin(self, plugin_name):
            if plugin_name in self.available_plugins:
                self.available_plugins[plugin_name]["status"] = "loaded"
                return True
            return False

        def execute_plugin_function(self, plugin_name: str, function_name: str, *args, **kwargs) -> dict:
            if plugin_name == "Anomaly Detector AI":
                # For this dummy, we can call the actual anomaly_entry function directly IF it's in path
                # Or, even better, simulate its output
                print(f"[DummyPM] Simulating sandboxed execution of {plugin_name}.{function_name}")
                event_data = args[0]
                is_anomaly = random.random() < 0.3 # Simulate 30% chance of anomaly
                anomaly_score = random.uniform(0.0, 1.0) if is_anomaly else random.uniform(0.0, 0.4)
                return {
                    "event_id": event_data.get("id", "N/A"),
                    "timestamp": time.time(),
                    "anomaly_score": round(anomaly_score, 3),
                    "is_anomaly": is_anomaly,
                    "prediction_confidence": round(random.uniform(0.6, 0.95), 3),
                    "suggested_action": "Simulated Investigate" if is_anomaly else "Simulated Monitor"
                }
            return {"error": "Plugin not found or function not implemented in dummy manager."}

    # Instantiate with dummy plugin manager for local test
    dummy_manager = DummyPluginManager()
    blue_team_ai = BlueTeamAI(dummy_manager)
    
    # Run a short defense cycle simulation
    async def main():
        # Override the check in BlueTeamAI init for this specific test
        # to ensure the dummy plugin is treated as loaded.
        blue_team_ai.loaded_anomaly_detector = dummy_manager.load_plugin(blue_team_ai.anomaly_detector_plugin_name)
        
        if blue_team_ai.loaded_anomaly_detector:
            print("\nStarting simulated defense cycle (will run for a few events)...")
            event_count = 0
            async for event in blue_team_ai.monitor_traffic_stream(1):
                await blue_team_ai.analyze_traffic_for_anomalies(event)
                event_count += 1
                if event_count >= 5: # Stop after 5 events for testing
                    break
        else:
            print("Anomaly Detector AI plugin not available in dummy manager for integrated testing.")

    # To run the async main function
    asyncio.run(main())
