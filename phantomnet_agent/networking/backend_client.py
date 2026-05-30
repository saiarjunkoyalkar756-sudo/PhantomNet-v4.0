import asyncio
import websockets
import json
import ssl
from typing import List
from pathlib import Path

from attestation import generate_attestation_payload

# Define paths to the certificates
CERT_PATH = Path(__file__).parent.parent / "certs"
CA_CERT = CERT_PATH / "ca.crt"
AGENT_CERT = CERT_PATH / "agent" / "agent.crt"
AGENT_KEY = CERT_PATH / "agent" / "agent.key"


class BackendClient:
    def __init__(self, agent_id: str, uri: str, event_queue: asyncio.Queue):
        self.agent_id = agent_id
        self.uri = uri.replace("ws://", "wss://").replace("http://", "https://")
        self.event_queue = event_queue
        self.websocket: websockets.WebSocketClientProtocol = None
        self.running = False
        self.ssl_context = self._create_ssl_context()
        self.offline_queue: List[dict] = []  # Local event queue for offline operation

    def _create_ssl_context(self) -> ssl.SSLContext:
        """Creates an SSL context for mTLS."""
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(CA_CERT)
            context.load_cert_chain(certfile=AGENT_CERT, keyfile=AGENT_KEY)
            print("Successfully created SSL context for mTLS.")
            return context
        except FileNotFoundError as e:
            print(f"ERROR: Certificate file not found for mTLS: {e}. Communication will be insecure.")
            return None
        except Exception as e:
            print(f"ERROR: Failed to create SSL context: {e}. Communication will be insecure.")
            return None

    async def connect(self):
        """Connects to the backend and performs identity attestation."""
        if not self.ssl_context:
            raise ConnectionError("Cannot establish secure connection: SSL context is not available.")
            
        self.websocket = await websockets.connect(self.uri, ssl=self.ssl_context)
        self.running = True
        print(f"Securely connected to backend at {self.uri}. Performing attestation...")

        # Step 1: Send attestation payload immediately after connecting
        attestation_payload = generate_attestation_payload()
        attestation_payload["agent_id"] = self.agent_id # Add agent_id to the payload
        await self.websocket.send(json.dumps(attestation_payload))

        # Step 2: Wait for an approval from the backend
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            response_data = json.loads(response)
            if response_data.get("status") != "attestation_approved":
                raise ConnectionRefusedError(f"Agent attestation failed: {response_data.get('reason', 'Unknown')}")
            print("Agent identity attestation approved by backend.")
        except asyncio.TimeoutError:
            raise ConnectionRefusedError("Attestation approval not received from backend.")

    async def run(self):
        retry_delay = 1.0
        max_delay = 60.0
        backoff_factor = 2.0

        while self.running:
            try:
                if not self.websocket or self.websocket.closed:
                    print(f"Connection lost. Attempting to reconnect (delay: {retry_delay}s)...")
                    await self.connect()
                    # Reset backoff on successful connection
                    retry_delay = 1.0

                    # Flush offline queue events first
                    if self.offline_queue:
                        print(f"Flushing {len(self.offline_queue)} buffered offline events...")
                        while self.offline_queue:
                            off_event = self.offline_queue[0]
                            await self.websocket.send(json.dumps(off_event))
                            self.offline_queue.pop(0)
                        print("All offline events successfully flushed.")
                
                event = await self.event_queue.get()
                try:
                    if not self.websocket or self.websocket.closed:
                        self.offline_queue.append(event)
                        print(f"Offline: Buffered event locally. Buffered count: {len(self.offline_queue)}")
                        self.event_queue.task_done()
                    else:
                        await self.websocket.send(json.dumps(event))
                        self.event_queue.task_done()
                except Exception as send_err:
                    self.offline_queue.append(event)
                    print(f"Send failed, buffering event locally. Error: {send_err}")
                    self.event_queue.task_done()
                    raise

            except (ConnectionRefusedError, ConnectionError, websockets.exceptions.InvalidURI, websockets.exceptions.ConnectionClosed) as e:
                print(f"Connection error: {e}. Retrying in {retry_delay} seconds.")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * backoff_factor, max_delay)
            except Exception as e:
                print(f"An unexpected error occurred in the run loop: {e}. Retrying in {retry_delay} seconds.")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * backoff_factor, max_delay)

    def start(self):
        """Starts the backend client connection loop."""
        self.running = True
        asyncio.create_task(self.run())

    def stop(self):
        """Stops the backend client."""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())
