import asyncio
import logging
import json
import random
import socket
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

from core.state import get_agent_state
from utils.logger import get_logger # Use the structured logger

class P2PNode:
    """
    An asyncio-based P2P Node implementing a conceptual gossip protocol.
    It discovers peers, exchanges agent status, and ingests relevant events into the Orchestrator.
    """
    def __init__(self, host: str, port: int, orchestrator: 'Orchestrator', gossip_interval: int = 10):
        self.logger = get_logger("phantomnet_agent.p2p_communication")
        self.host = host
        self.port = port
        self.orchestrator = orchestrator
        self.gossip_interval = gossip_interval
        self.peers: Dict[Tuple[str, int], datetime] = {} # { (ip, port): last_seen_datetime }
        self.known_agents: Dict[str, Dict[str, Any]] = {} # { agent_id: { last_seen, status, etc. } }
        self.stop_event = asyncio.Event()
        self._listener_task: Optional[asyncio.Task] = None
        self._gossiper_task: Optional[asyncio.Task] = None
        self.transport: Optional[asyncio.DatagramProtocol] = None

        self.logger.info(f"P2PNode initialized on {self.host}:{self.port} with gossip interval {self.gossip_interval}s.")

    async def start(self):
        """Starts the P2P node's listener and gossiper tasks."""
        loop = asyncio.get_running_loop()
        self.transport, protocol = await loop.create_datagram_endpoint(
            lambda: P2PProtocol(self),
            local_addr=(self.host, self.port)
        )
        self.logger.info(f"P2P UDP listener started on {self.host}:{self.port}.")
        self._gossiper_task = asyncio.create_task(self._gossip_loop())
        self.logger.info("P2P gossiper started.")

    async def stop(self):
        """Stops the P2P node's tasks."""
        self.logger.info("P2PNode stopping...")
        self.stop_event.set()
        if self._gossiper_task:
            self._gossiper_task.cancel()
            await asyncio.gather(self._gossiper_task, return_exceptions=True)
        if self.transport:
            self.transport.close()
            self.logger.info("P2P UDP listener closed.")
        self.logger.info("P2PNode stopped.")

    async def _gossip_loop(self):
        """Periodically sends gossip messages to known peers and discovers new ones."""
        while not self.stop_event.is_set():
            await self._discover_peers()
            await self._gossip_status()
            await asyncio.sleep(self.gossip_interval)

    async def _discover_peers(self):
        """Simulates peer discovery by scanning a local subnet or using a rendezvous point."""
        agent_state = get_agent_state()
        local_ip_prefix = ".".join(self.host.split('.')[:-1])
        self.logger.debug(f"Attempting to discover peers in {local_ip_prefix}.x...")
        
        discovery_message = {
            "type": "p2p_discovery",
            "sender_agent_id": agent_state.agent_id,
            "sender_address": (self.host, self.port),
            "timestamp": datetime.now().isoformat()
        }
        message_bytes = json.dumps(discovery_message).encode()

        # Simple broadcast to a few common local IPs for conceptual discovery
        for i in range(1, 10): # Check a small range
            peer_ip = f"{local_ip_prefix}.{random.randint(1, 254)}"
            if peer_ip != self.host:
                try:
                    self.transport.sendto(message_bytes, (peer_ip, self.port))
                    self.logger.debug(f"Sent discovery to {peer_ip}:{self.port}")
                except Exception as e:
                    self.logger.debug(f"Could not send discovery to {peer_ip}:{self.port}: {e}")
        
        # Clean up old peers
        cutoff_time = datetime.now() - timedelta(seconds=self.gossip_interval * 3)
        self.peers = {peer: last_seen for peer, last_seen in self.peers.items() if last_seen > cutoff_time}


    async def _gossip_status(self):
        """Gossip current agent status and known peers to a random subset of peers."""
        if not self.peers:
            return

        agent_state = get_agent_state()
        current_status = {
            "agent_id": agent_state.agent_id,
            "status": agent_state.status, # Use new status attribute
            "mode": agent_state.mode,
            "last_heartbeat": agent_state.last_heartbeat.isoformat(),
            "known_peers": [(p[0], p[1]) for p in self.peers.keys()], # Send list of known peer addresses
            "known_agents_summary": {aid: {'last_seen': data['last_seen'], 'status': data['status']} for aid, data in self.known_agents.items()}
        }
        gossip_message = {
            "type": "p2p_gossip",
            "sender_agent_id": agent_state.agent_id,
            "sender_address": (self.host, self.port),
            "status_update": current_status,
            "timestamp": datetime.now().isoformat()
        }
        message_bytes = json.dumps(gossip_message).encode()

        # Select a random subset of peers to gossip to
        peers_to_gossip_to = random.sample(list(self.peers.keys()), min(len(self.peers), 3)) # Gossip to 3 random peers
        for peer_addr in peers_to_gossip_to:
            try:
                self.transport.sendto(message_bytes, peer_addr)
                self.logger.debug(f"Sent gossip to {peer_addr}")
            except Exception as e:
                self.logger.debug(f"Could not send gossip to {peer_addr}: {e}")

    async def _handle_message(self, data: bytes, addr: Tuple[str, int]):
        """Handles incoming P2P messages."""
        try:
            message = json.loads(data.decode())
            message_type = message.get("type")
            sender_agent_id = message.get("sender_agent_id", "unknown")

            self.peers[addr] = datetime.now() # Mark peer as seen
            
            if message_type == "p2p_discovery":
                self.logger.debug(f"Received discovery from {sender_agent_id} at {addr}")
                self.logger.info("P2P_PEER_DISCOVERY", extra={"peer_agent_id": sender_agent_id, "peer_address": addr}) # Use structured logging
                # Immediately respond with our status to new peer
                agent_state = get_agent_state()
                response_status = {
                    "agent_id": agent_state.agent_id,
                    "status": agent_state.status, # Use new status attribute
                    "mode": agent_state.mode,
                    "last_heartbeat": agent_state.last_heartbeat.isoformat(),
                }
                response_message = {
                    "type": "p2p_status_response",
                    "sender_agent_id": agent_state.agent_id,
                    "sender_address": (self.host, self.port),
                    "status_update": response_status,
                    "timestamp": datetime.now().isoformat()
                }
                self.transport.sendto(json.dumps(response_message).encode(), addr)
                self.logger.debug(f"Sent status response to new peer {addr}")

            elif message_type == "p2p_gossip" or message_type == "p2p_status_response":
                self.logger.debug(f"Received {message_type} from {sender_agent_id} at {addr}")
                status_update = message.get("status_update", {})
                if status_update:
                    # Update our knowledge about this agent
                    self.known_agents[sender_agent_id] = {
                        "last_seen": datetime.now().isoformat(),
                        "status": status_update.get("status"),
                        "mode": status_update.get("mode"),
                        "last_heartbeat": status_update.get("last_heartbeat"),
                        "address": addr
                    }
                    self.logger.info("P2P_AGENT_STATUS_UPDATE", extra={"agent_id": sender_agent_id, "status_data": status_update}) # Use structured logging
                    
                    # Merge known peers and agents (conceptual for simplicity)
                    if message_type == "p2p_gossip":
                        for peer_ip, peer_port in status_update.get("known_peers", []):
                            peer_tuple = (peer_ip, peer_port)
                            if peer_tuple not in self.peers and peer_tuple != (self.host, self.port):
                                self.peers[peer_tuple] = datetime.now()
                                self.logger.debug(f"Discovered new peer {peer_tuple} from gossip.")
                        
                        for aid, agent_summary in status_update.get("known_agents_summary", {}).items():
                            if aid not in self.known_agents and aid != get_agent_state().agent_id:
                                self.known_agents[aid] = agent_summary
                                self.known_agents[aid]['address'] = (agent_summary['address'][0], agent_summary['address'][1]) if isinstance(agent_summary['address'], list) else agent_summary['address'] # Ensure tuple
                                self.logger.debug(f"Learned about new agent {aid} from gossip.")

            elif message_type == "p2p_alert":
                self.logger.info(f"Received P2P alert from {sender_agent_id} at {addr}: {message.get('alert_data')}")
                # Ingest alert into Orchestrator
                alert_event = {
                    "event_type": "P2P_ALERT",
                    "source": "p2p_network",
                    "sender_agent_id": sender_agent_id,
                    "sender_address": addr,
                    "alert_data": message.get("alert_data"),
                    "timestamp": datetime.now().isoformat()
                }
                await self.orchestrator.ingest_event(alert_event)
            else:
                self.logger.warning(f"Received unknown P2P message type from {addr}: {message_type}")

        except json.JSONDecodeError:
            self.logger.warning(f"Received malformed JSON message from {addr}.")
        except Exception as e:
            self.logger.error(f"Error handling P2P message from {addr}: {e}", exc_info=True)


class P2PProtocol(asyncio.DatagramProtocol):
    """Asyncio UDP protocol to receive data for the P2PNode."""
    def __init__(self, node: P2PNode):
        self.node = node
        self.transport: Optional[asyncio.DatagramTransport] = None
        self.logger = self.node.logger # Use the node's logger

    def connection_made(self, transport: asyncio.BaseTransport):
        self.transport = transport
        self.logger.debug("P2P UDP Protocol connection made.")

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        asyncio.create_task(self.node._handle_message(data, addr))

    def error_received(self, exc: Exception):
        self.logger.error(f"P2P UDP error received: {exc}")

    def connection_lost(self, exc: Optional[Exception]):
        if exc:
            self.logger.warning(f"P2P UDP connection lost: {exc}")
        else:
            self.logger.info("P2P UDP connection closed.")

# Example usage (for testing, not part of actual runtime)
async def main():
    logging.basicConfig(level=logging.DEBUG)

    # Mock Orchestrator for testing
    class MockOrchestrator:
        def __init__(self):
            self.events = []
        async def ingest_event(self, event: Dict[str, Any]):
            logger.info(f"Mock Orchestrator ingested P2P event: {event.get('event_type')}")
            self.events.append(event)
    
    # Initialize agent state for mocking
    from core.config import AgentConfig, Config
    from core.state import initialize_agent_state
    initialize_agent_state("test-agent-p2p", "full")
    agent_state = get_agent_state()
    agent_state.config = Config(agent=AgentConfig(
        id="test-agent-p2p", manager_url="http://localhost:8001",
        collectors={}, plugins={}, bus={"type": "http", "http": {"endpoint": "http://localhost:8001"}},
        log_level="INFO", heartbeat_interval=30
    ))
    agent_state.last_heartbeat = datetime.now() # Mock a heartbeat
    agent_state.is_running = True


    # Create two P2P nodes (e.g., in different terminals)
    # Node 1
    node1_orchestrator = MockOrchestrator()
    node1 = P2PNode(host="127.0.0.1", port=8005, orchestrator=node1_orchestrator)
    await node1.start()

    # Node 2 (run this in a separate process/terminal to see P2P in action)
    # node2_orchestrator = MockOrchestrator()
    # node2 = P2PNode(host="127.0.0.1", port=8006, orchestrator=node2_orchestrator)
    # await node2.start()

    # Simulate some time for gossip and discovery
    print("\nRunning P2P nodes for 30 seconds. Look for discovery and gossip messages.")
    await asyncio.sleep(30)

    # Simulate an alert being sent from node1
    print("\nSimulating P2P alert from node1...")
    await node1.transport.sendto(json.dumps({
        "type": "p2p_alert",
        "sender_agent_id": agent_state.agent_id,
        "sender_address": (node1.host, node1.port),
        "alert_data": {"threat_type": "DDoS", "target_ip": "10.0.0.1"},
        "timestamp": datetime.now().isoformat()
    }).encode(), ("127.0.0.1", 8005)) # Sending to itself for demo, normally to a peer

    await asyncio.sleep(5) # Give time for alert to be processed

    await node1.stop()
    # await node2.stop() # If node2 was started

    print("\nNode 1 ingested events:")
    for event in node1_orchestrator.events:
        print(event)

if __name__ == "__main__":
    asyncio.run(main())