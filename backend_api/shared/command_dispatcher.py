import asyncio
import uuid
import json
import httpx # For simulating calls to agents via API Gateway
from typing import Dict, Any, Optional
from loguru import logger

# Assuming schemas are available
from .schemas import AgentConfiguration # Example schema for config push

class CommandDispatcher:
    def __init__(self, api_gateway_url: str = "http://localhost:8000"):
        self.command_queue = asyncio.Queue()
        self.api_gateway_url = api_gateway_url
        logger.info(f"CommandDispatcher initialized, targeting API Gateway at {self.api_gateway_url}")

    async def enqueue_command(self, agent_id: str, command_type: str, payload: Dict[str, Any], initiated_by: str = "SOAR_Engine"):
        """
        Enqueues a command to be dispatched to an agent.
        """
        command_id = str(uuid.uuid4())
        command = {
            "command_id": command_id,
            "agent_id": agent_id,
            "command_type": command_type, # e.g., "isolate_host", "terminate_process", "get_status", "update_config"
            "payload": payload,
            "status": "queued",
            "timestamp": time.time(),
            "initiated_by": initiated_by,
        }
        await self.command_queue.put(command)
        logger.info(f"Command {command_id} enqueued for agent {agent_id}. Type: {command_type}")
        return command_id

    async def _dispatch_command_to_agent(self, command: Dict[str, Any]):
        """
        Simulates securely delivering a command to an agent via the PN_API_Gateway.
        """
        agent_id = command["agent_id"]
        command_type = command["command_type"]
        payload = command["payload"]
        command_id = command["command_id"]

        logger.debug(f"Dispatching command {command_id} (Type: {command_type}) to agent {agent_id}...")

        # --- Security Considerations for Command Delivery ---
        # In a real system, this would involve:
        # 1. Digital Signing: The command payload would be signed by the Command Dispatcher's private key.
        # 2. Encryption: The payload might be encrypted using the agent's public key or a session key.
        # 3. Secure Transport: The API Gateway (and underlying service mesh) would ensure mTLS.
        # 4. Agent Authentication: The agent receiving the command would authenticate the dispatcher
        #    and verify the command's signature before execution.
        #
        # For this mock, we simulate an HTTP call to the API Gateway's agent-facing endpoint.

        agent_command_endpoint = f"{self.api_gateway_url}/agents/{agent_id}/command" # Conceptual endpoint
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    agent_command_endpoint,
                    json={
                        "command_type": command_type,
                        "payload": payload,
                        "command_id": command_id,
                        # "signature": "mock_signature_of_payload", # Placeholder
                        # "encrypted_payload": "mock_encrypted_payload" # Placeholder
                    },
                    timeout=5.0
                )
                response.raise_for_status()
                logger.info(f"Command {command_id} dispatched successfully to agent {agent_id}. Status: {response.status_code}")
                # Update command status in a persistent store
                return {"status": "success", "response": response.json()}
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to dispatch command {command_id} to agent {agent_id} - HTTP Error: {e.response.status_code} {e.response.text}")
            return {"status": "failed", "detail": f"HTTP Error: {e.response.status_code} {e.response.text}"}
        except httpx.RequestError as e:
            logger.error(f"Failed to dispatch command {command_id} to agent {agent_id} - Network Error: {e}")
            return {"status": "failed", "detail": f"Network Error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error dispatching command {command_id} to agent {agent_id}: {e}")
            return {"status": "failed", "detail": f"Unexpected error: {e}"}


    async def start_dispatching(self):
        """
        Starts the continuous command dispatching process.
        """
        logger.info("CommandDispatcher starting command dispatching loop...")
        while True:
            command = await self.command_queue.get()
            logger.debug(f"Processing command from queue: {command['command_id']}")
            
            # Dispatch the command (simulated)
            dispatch_result = await self._dispatch_command_to_agent(command)
            
            # Log or handle dispatch result (e.g., update command status in DB)
            if dispatch_result["status"] == "failed":
                logger.error(f"Command {command['command_id']} dispatch failed: {dispatch_result['detail']}")
            
            self.command_queue.task_done()
            await asyncio.sleep(0.1) # Small delay to prevent busy-looping

# Example Usage
if __name__ == "__main__":
    dispatcher = CommandDispatcher()

    async def test_dispatcher():
        asyncio.create_task(dispatcher.start_dispatching())

        # Enqueue some commands
        await dispatcher.enqueue_command("agent-123", "isolate_host", {"hostname": "infected_server_01"})
        await dispatcher.enqueue_command("agent-456", "terminate_process", {"hostname": "user_pc_02", "process_name": "malware.exe"})
        await dispatcher.enqueue_command("agent-123", "update_config", {"config_data": AgentConfiguration(reporting_interval_seconds=60)})
        
        # Simulate an agent response (this would normally come back to a different endpoint)
        async def mock_agent_command_endpoint():
            class MockResponse:
                def __init__(self, status_code, json_data):
                    self.status_code = status_code
                    self._json_data = json_data
                async def json(self):
                    return self._json_data
                def raise_for_status(self):
                    if self.status_code >= 400:
                        raise httpx.HTTPStatusError("Bad Request", request=httpx.Request("POST", "/"), response=self)

            # Mock for httpx.AsyncClient.post
            def mock_post(*args, **kwargs):
                cmd_type = kwargs['json']['command_type']
                agent_id_from_url = args[0].split('/')[-2]
                if cmd_type == "isolate_host" and agent_id_from_url == "agent-123":
                    return MockResponse(200, {"status": "success", "agent_response": "Host isolated"})
                elif cmd_type == "terminate_process":
                    return MockResponse(200, {"status": "success", "agent_response": "Process terminated"})
                elif cmd_type == "update_config":
                    return MockResponse(200, {"status": "success", "agent_response": "Config updated"})
                return MockResponse(404, {"status": "failed", "detail": "Command not found or agent not responsive"})

            httpx.AsyncClient.post = mock_post # Patch httpx.AsyncClient.post

            # This is a very rough mock. In a real scenario, the agent would have an actual HTTP endpoint
            # that the API Gateway routes to, and then the agent executes the command.
            # For testing the dispatcher, we're just simulating the API Gateway's call to that agent endpoint.
            logger.info("Mock agent command endpoint active.")


        await mock_agent_command_endpoint() # Set up the mock
        await asyncio.sleep(5) # Let commands dispatch
        print("\n--- Test Dispatcher Finished ---")

    asyncio.run(test_dispatcher())
