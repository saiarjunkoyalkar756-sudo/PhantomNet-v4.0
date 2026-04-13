import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx # Import httpx for making HTTP requests


import uvicorn
from fastapi import FastAPI

# Core Components

from core.config import load_config

from core.logging_config import setup_logging

from core.state import initialize_agent_state, get_agent_state



# Bus Transports

from bus.base import Transport

from bus.http_bus import HttpTransport

from bus.redis_bus import RedisTransport

from bus.kafka_bus import KafkaTransport







# Collectors



from collectors.base import Collector # Import Collector base class



from collectors.process_collector import ProcessCollector



from collectors.file_collector import FileCollector



from collectors.network_collector import NetworkCollector



from collectors.dns_collector import DnsCollector



from collectors.log_collector import LogCollector



from collectors.container_collector import ContainerCollector



from collectors.self_monitor_collector import SelfMonitorCollector



from collectors.windows_registry_monitor import WindowsRegistryMonitor



from ebpf_process_monitor import EbpfProcessMonitor



from ebpf_file_monitor import EbpfFileMonitor



from ebpf_driver_monitor import EbpfDriverMonitor



from collectors.ebpf_simulator import EbpfSimulator # Import the eBPF simulator



from collectors.memory_scanner import MemoryScanner



from collectors.software_collector import SoftwareCollector







# Actions

from actions.base import Action

from actions.process_actions import ProcessActions

from actions.network_actions import NetworkActions

from actions.system_actions import SystemActions



# Plugins

from plugins.loader import PluginLoader, Plugin

from plugins.sandbox import PluginSandbox



# API

from api.health_api import router as health_router

from api.control_api import router as control_router

from api.log_streaming_api import router as log_streaming_router, manager as log_streaming_manager



# Log Forwarder

from phantomnet_agent.log_forwarder import LogForwarder

from self_healing_infrastructure import AgentHealthMonitor

from orchestrator import Orchestrator # Import the Orchestrator

from telemetry_collector import TelemetryCollector # Import the new TelemetryCollector

from generate_certs import generate_agent_identity, CERT_DIR, AGENT_KEY_NAME, AGENT_CERT_NAME # For generating agent identity

from security.jwt_manager import JWTManager # For JWT token generation
from shared.platform_utils import IS_WINDOWS, IS_LINUX, IS_TERMUX, IS_ROOT, HAS_PCAP, HAS_EBPF, CAN_BIND_LOW_PORTS, ARCH, PLATFORM_INFO, get_platform_details, SAFE_MODE, SUPPORTS_RAW_SOCKETS
from phantomnet_agent.platform_compatibility.os_detector import OSDetector
from phantomnet_agent.platform_compatibility.linux_adapter import LinuxAdapter
from phantomnet_agent.platform_compatibility.windows_adapter import WindowsAdapter
from phantomnet_agent.platform_compatibility.termux_adapter import TermuxAdapter



from datetime import datetime






# Cryptography for agent identity and mTLS



from cryptography import x509

from cryptography.hazmat.primitives import serialization



from cryptography.hazmat.primitives.asymmetric import rsa



from cryptography.hazmat.backends import default_backend





# Initialize a global logger for main.py



logger = logging.getLogger("phantomnet_agent.main")



COLLECTOR_CLASSES = {



    "process": ProcessCollector,



    "file": FileCollector,



    "network": NetworkCollector,



    "dns": DnsCollector,



    "logs": LogCollector,



    "container": ContainerCollector,



    "self_monitor": SelfMonitorCollector, # Add SelfMonitorCollector



    "windows_registry": WindowsRegistryMonitor,



    "memory_scanner": MemoryScanner,



    # Conditional eBPF collectors



    "ebpf_process": EbpfProcessMonitor,



    "ebpf_file": EbpfFileMonitor,



    "ebpf_driver": EbpfDriverMonitor,



    "ebpf_simulator": EbpfSimulator,



    "software": SoftwareCollector,



}







ACTION_CLASSES = {



    "process_actions": ProcessActions,



    "network_actions": NetworkActions,



    "system_actions": SystemActions,



}







def _get_collector_capability_status(collector_name: str, agent_state: Any) -> str:



    """



    Determines if a collector should be enabled based on OS capabilities.



    Returns "enabled", "disabled_by_os", "disabled_by_config", or "fallback_to_simulator".



    """



    global IS_WINDOWS, IS_LINUX, IS_TERMUX, HAS_EBPF, SUPPORTS_RAW_SOCKETS, PLATFORM_INFO # Access global flags







    if collector_name == "ebpf_process" or collector_name == "ebpf_file" or collector_name == "ebpf_driver":



        if HAS_EBPF:



            return "enabled"



        else:



            return "fallback_to_simulator"



    elif collector_name == "ebpf_simulator":



        if HAS_EBPF: # If real eBPF is available, don't run simulator



            return "disabled_by_os"



        else: # Only run simulator if real eBPF is not available



            return "enabled"



    elif collector_name == "windows_registry":



        if not IS_WINDOWS:



            return "disabled_by_os"



    elif collector_name == "memory_scanner":



        # Memory scanner using YARA might be limited by OS capabilities (e.g., Termux)



        if PLATFORM_INFO["memory_scanner_method"] == "limited_mode":



            logger.warning(f"Collector '{collector_name}' will run in limited mode due to OS capabilities.")



    elif collector_name == "network":



        # Network sensor depends on raw socket support



        if not SUPPORTS_RAW_SOCKETS and PLATFORM_INFO["network_driver"] != "scapy_limited":



            return "disabled_by_os" # Scapy will run in limited mode, but eBPF+Scapy might fail.







    # Default to enabled if no specific OS-based disablement or fallback



    return "enabled"







async def initialize_transport(config: Any, agent_state: Any, jwt_manager: Optional[JWTManager] = None) -> Transport:

    """Initializes and returns the appropriate transport based on configuration."""

    bus_config = config.agent.bus

    if bus_config.type == "http":

        # Conceptual mTLS configuration for HttpTransport

        # In a real scenario, these paths would come from agent_state after registration,

        # or loaded from config if already provisioned.

        client_cert_path = getattr(agent_state, "cert_path", None) # Path to agent's signed client cert

        client_key_path = getattr(agent_state, "key_path", None) # Path to agent's private key

        ca_cert_path = getattr(config.agent, "mtls_ca_cert_path", None) # Path to CA cert for server verification



        return HttpTransport(

            endpoint=bus_config.http.get("endpoint"),

            client_cert=client_cert_path if all([client_cert_path, client_key_path]) else None,

            client_key=client_key_path if all([client_cert_path, client_key_path]) else None,

            verify_ca=ca_cert_path if ca_cert_path else True # Verify with specific CA or default trust store

        )

    elif bus_config.type == "redis":

        redis_config = bus_config.redis or {}

        return RedisTransport(

            url=redis_config.get("url"),

            events_channel=redis_config.get("events_channel"),

            commands_channel=redis_config.get("commands_channel")

        )

    elif bus_config.type == "kafka":

        kafka_config = bus_config.kafka or {}

        return KafkaTransport(

            bootstrap_servers=kafka_config.get("bootstrap_servers"),

            events_topic=kafka_config.get("events_topic"),

            commands_topic=kafka_config.get("commands_topic"),

            consumer_group_id=f"agent-{config.agent.id}" # Unique consumer group per agent

        )

    



async def run_collectors(agent_state: Any, orchestrator: Orchestrator):
    """Initializes and starts all enabled collectors."""
    config = agent_state.config.agent
    adapter = agent_state.adapter
    agent_state.collectors = {} # Clear existing collectors

    for collector_name, collector_config in config.collectors.items():
        if not collector_config.enabled:
            continue # Skip if collector is disabled in config
        
        capability_status = _get_collector_capability_status(collector_name, agent_state)

        if capability_status == "disabled_by_os":
            logger.warning(f"Collector '{collector_name}' is enabled in config but disabled by OS capabilities. Skipping.")
            continue
        elif capability_status == "fallback_to_simulator":
            if collector_name in ["ebpf_process", "ebpf_file", "ebpf_driver"]:
                logger.info(f"Collector '{collector_name}' is enabled but eBPF not supported. Falling back to EbpfSimulator.")
                # Ensure EbpfSimulator is enabled in config for it to be created
                if config.collectors.get("ebpf_simulator") and config.collectors["ebpf_simulator"].enabled:
                    # Create the simulator if it's not already running
                    if "ebpf_simulator" not in agent_state.collectors:
                        simulator_class = COLLECTOR_CLASSES.get("ebpf_simulator")
                        if simulator_class:
                            simulator_config = config.collectors["ebpf_simulator"].dict()
                            simulator = simulator_class(orchestrator, adapter, simulator_config)
                            agent_state.collectors["ebpf_simulator"] = simulator
                            asyncio.create_task(simulator.start())
                            logger.info("EbpfSimulator started.")
                else:
                    logger.warning(f"EbpfSimulator is not enabled in config. Cannot fallback for {collector_name}.")
            continue # Skip real eBPF collector
        
        collector_class = COLLECTOR_CLASSES.get(collector_name)

        if collector_class:
            logger.info(f"Initializing collector: {collector_name}")
            # Pass the orchestrator and adapter to the collector for event ingestion and OS interaction
            collector = collector_class(orchestrator, adapter, collector_config.dict()) 
            # Update agent_id in collector's internal events
            if hasattr(collector, "agent_id"):
                collector.agent_id = agent_state.agent_id
            agent_state.collectors[collector_name] = collector
            asyncio.create_task(collector.start()) # Run in background
        else:
            logger.warning(f"Unknown collector type in config: {collector_name}")



async def run_api(agent_state: Any, host: str = "127.0.0.1", port: int = 8000):

    """Starts the local FastAPI server for health and control."""

    app = FastAPI(title="PhantomNet Agent API")

    app.include_router(health_router, prefix="/api")

    app.include_router(control_router, prefix="/api")

    app.include_router(log_streaming_router, prefix="/api") # Include the log streaming router



    uvicorn_config = uvicorn.Config(app, host=host, port=port, log_level="warning")

    server = uvicorn.Server(uvicorn_config)

    

    # Run the server in a separate task

    logger.info(f"Starting local API at http://{host}:{port}/api/health")

    await server.serve()





async def register_agent_with_manager(agent_state: Any, config: Any, private_key_pem: str, public_key_pem: str, key_path: Path, cert_path: Path) -> bool:
    """
    Handles the agent registration process with the PN_Agent_Manager.
    Uses provided key pair to send public key and receive a signed certificate.
    """
    logger.info("Initiating agent registration with PN_Agent_Manager...")

    # 1. Prepare registration data with provided public key
    registration_data = {
        "public_key": public_key_pem,
        "role": getattr(config.agent, "role", "default_agent_role"),
        "version": getattr(config.agent, "version", "0.0.1"),
        "location": getattr(config.agent, "location", "unknown"),
        "bootstrap_token": getattr(config.agent, "bootstrap_token", None),
        "configuration": getattr(config.agent, "configuration", None).model_dump_json() if getattr(config.agent, "configuration", None) else None,
    }

    # 2. Send registration request to PN_Agent_Manager
    agent_manager_url = str(config.agent.manager_url) + "/agents/register"

    try:
        # Use httpx.AsyncClient with mTLS if enabled and certs are available
        client_kwargs = {}
        if getattr(config.agent.security, 'tls', None) and config.agent.security.tls.enabled: # Assuming mTLS is enabled in config
            # ca_cert_path would come from config.agent.security.tls.ca_cert_path
            ca_cert_path = getattr(config.agent.security.tls, "ca_cert_path", None)
            if cert_path and key_path and ca_cert_path:
                 client_kwargs["cert"] = (str(cert_path), str(key_path))
                 client_kwargs["verify"] = str(ca_cert_path)
            else:
                logger.warning("mTLS is enabled in config but cert/key/CA paths are not fully configured. Proceeding without mTLS for registration.")

        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.post(agent_manager_url, json=registration_data, timeout=10.0)
            response.raise_for_status()
            registration_result = response.json()
        
        # 3. Store signed certificate and agent ID
        agent_state.agent_id = registration_result["agent"]["id"]
        agent_state.signed_certificate_pem = registration_result["certificate"]
        
        # Save received signed cert to file (overwriting temporary self-signed if needed)
        cert_path.write_text(agent_state.signed_certificate_pem)
        agent_state.cert_path = str(cert_path) # Update agent_state with path to signed cert
        agent_state.key_path = str(key_path) # Ensure key path is also stored

        logger.info(f"Agent '{agent_state.agent_id}' registered successfully. Certificate received.")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(f"Agent registration failed - HTTP Error: {e.response.status_code} {e.response.text}", extra={"error": str(e)})
    except httpx.RequestError as e:
        logger.error(f"Agent registration failed - Network Error: {e}", extra={"error": str(e)})
    except Exception as e:
        logger.error(f"Agent registration failed: {e}", exc_info=True, extra={"error": str(e)})
    return False



async def main_loop(config: Any, transport: Transport, actions: Dict[str, Action], plugins: Dict[str, Plugin], orchestrator: Orchestrator):

    """Main agent loop for receiving commands and dispatching to actions/plugins."""

    agent_state = get_agent_state()

    logger.info(f"Agent '{agent_state.agent_id}' entering main loop in mode: {agent_state.mode}")

    # Use an event to signal shutdown
    shutdown_event = asyncio.Event()

    async def shutdown_handler():
        logger.info("Shutdown signal received. Initiating graceful shutdown...")
        shutdown_event.set()

    # Register signal handlers for graceful shutdown (Unix-like systems)
    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown_handler()))
    else:
        logger.warning("Signal handling not fully implemented for Windows. Use Ctrl+C to terminate.")

    # Main loop for receiving commands
    try:
        # Determine the correct commands topic based on the bus type
        commands_topic = ""
        if config.agent.bus.type == "redis":
            commands_topic = config.agent.bus.redis.get("commands_channel")
        elif config.agent.bus.type == "kafka":
            commands_topic = config.agent.bus.kafka.get("commands_topic")
        elif config.agent.bus.type == "http":
            logger.info("HTTP transport is configured for outbound events only; skipping command reception loop.")
            # We don't actively listen for commands over HTTP in this implementation.
            # The agent will continue to run and send events as configured by collectors.
            # This loop will effectively become a passive wait or rely on external triggers.
            while not shutdown_event.is_set():
                await asyncio.sleep(1) # Keep the event loop alive
            return # Exit main_loop for HTTP transport

        async for command in transport.receive_commands(commands_topic):
            if shutdown_event.is_set():
                break # Exit if shutdown requested

            logger.info(f"Received command: {command.action_type} (ID: {command.action_id})")
            
            # Encapsulate command as an event and ingest into the orchestrator
            command_event = {
                "event_type": "AGENT_COMMAND",
                "command_id": command.action_id,
                "command_type": command.action_type,
                "payload": command.payload,
                "timestamp": datetime.now().isoformat(),
                "source": "command_bus"
            }
            await orchestrator.ingest_event(command_event)
            logger.info(f"Command '{command.action_id}' ingested into Orchestrator.")
            
            # The actual execution and result handling for commands will now be
            # managed by the Orchestrator's event processing pipeline, potentially
            # involving plugins or other components within the orchestrator.
            # So, the direct action dispatching logic here is removed.

            await asyncio.sleep(0.1) # Prevent busy loop if command stream is very fast
    except Exception as e:
        logger.critical(f"Error in main agent loop: {e}", exc_info=True)
    finally:
        # Wait for shutdown event if not already set (e.g., if loop exited prematurely)
        if not shutdown_event.is_set():
            await shutdown_event.wait()

    logger.info("Main agent loop exited.")


async def main():
    parser = argparse.ArgumentParser(description="PhantomNet Agent")
    parser.add_argument("--config", type=Path, default=Path("config/agent.yml"),
                        help="Path to the agent configuration file.")
    parser.add_argument("--mode", type=str, default="full",
                        choices=["full", "collector-only", "forensics", "osint", "dry-run"],
                        help="Operating mode of the agent.")
    parser.add_argument("--api-host", type=str, default="127.0.0.1",
                        help="Host for the local API.")
    parser.add_argument("--api-port", type=int, default=8000,
                        help="Port for the local API.")
    
    args = parser.parse_args()

    # 1. Load config
    config = load_config(args.config)
    if not config:
        print(f"ERROR: Failed to load or validate configuration from {args.config}", file=sys.stderr)
        sys.exit(1)
    
    # Override mode from CLI if provided
    config.agent.mode = args.mode

    # 2. Initialize logging
    global logger
    logger = setup_logging(config.agent.log_level, config.agent.id, config.agent.mode)
    logger.info(f"Starting PhantomNet Agent (ID: {config.agent.id}, Mode: {config.agent.mode})")
    logger.info(f"Detected Platform: {PLATFORM_INFO['os_type']} ({PLATFORM_INFO['architecture']})")
    logger.info(f"Is Root/Admin: {IS_ROOT}, SAFE_MODE: {SAFE_MODE}")
    logger.info(f"Platform Capabilities: {PLATFORM_INFO}")

    # --- Security Check: Insecure Defaults ---
    if config.agent.manager_url == "http://localhost:8000":
        logger.critical("!!! INSECURE CONFIGURATION DETECTED !!!")
        logger.critical("!!! SECURITY WARNING: AGENT_MANAGER_URL is set to default insecure value (http://localhost:8000). CHANGE THIS IN config/agent.yml for production deployments. !!!")
        logger.critical("!!! Please update your config/agent.yml file. !!!")
    # --- End Security Check ---

    # 3. Initialize agent state
    agent_state = initialize_agent_state(
        agent_id=config.agent.id,
        mode=config.agent.mode,
        os_type=PLATFORM_INFO["os_type"],
        capabilities=PLATFORM_INFO
    )
    agent_state.config = config # Store config in state for easy access by other components
    agent_state.started_at = datetime.now() # Set agent startup time

    # 4. Initialize OS-specific adapter
    os_detector = OSDetector()
    adapter = os_detector.get_adapter()
    if not adapter:
        logger.critical("Unsupported OS, exiting.")
        sys.exit(1)
    agent_state.adapter = adapter
    logger.info(f"OS adapter loaded: {type(adapter).__name__}")

    # Generate or load agent identity (private key and certificate)
    agent_id = agent_state.agent_id
    key_path = CERT_DIR / f"{agent_id}.key"
    cert_path = CERT_DIR / f"{agent_id}.pem"
    
    # Ensure CERT_DIR exists before generating
    CERT_DIR.mkdir(parents=True, exist_ok=True)

    private_key_pem: Optional[str] = None
    public_key_pem: Optional[str] = None
    
    try:
        if not key_path.exists() or not cert_path.exists():
            # Only generate if they don't exist
            _, _ = await generate_agent_identity(agent_id, agent_id, key_path, cert_path)
        
        with open(key_path, 'r') as f:
            private_key_pem = f.read()
        
        # Load the certificate and extract the public key
        with open(cert_path, 'rb') as f: # Open in binary mode for x509.load_pem_x509_certificate
            cert_data = f.read()
            certificate = x509.load_pem_x509_certificate(cert_data, default_backend())
            public_key = certificate.public_key()
            # Serialize the public key to PEM format
            public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
        
        # Store paths to cert and key in agent_state for mTLS if needed
        agent_state.cert_path = str(cert_path)
        agent_state.key_path = str(key_path)

        logger.info("Agent identity loaded/generated successfully.")
    except Exception as e:
        logger.critical(f"Failed to generate or load agent identity: {e}", exc_info=True)
        sys.exit(1)

    # Initialize JWT Manager
    jwt_manager = None
    if private_key_pem and public_key_pem:
        try:
            jwt_manager = JWTManager(private_key_pem, public_key_pem, agent_id)
            agent_state.jwt_manager = jwt_manager # Store JWT manager in state
            logger.info("JWT Manager initialized.")
        except Exception as e:
            logger.critical(f"Failed to initialize JWT Manager: {e}", exc_info=True)
            sys.exit(1)

    # Initialize Log Forwarder
    backend_url = str(config.agent.manager_url) # Using manager_url as backend for logs
    agent_id = agent_state.agent_id # From registration or fallback
    
    # Get the root logger to add LogForwarder as a handler
    root_logger = logging.getLogger("phantomnet_agent") # Get the logger configured by setup_logging
    
    log_forwarder_handler = LogForwarder(
        backend_url=backend_url, 
        agent_id=agent_id, 
        level=root_logger.level
    )
    root_logger.addHandler(log_forwarder_handler)
    log_forwarder_task = asyncio.create_task(log_forwarder_handler.start())
    logger.info("Log Forwarder initialized and started.")

    # Initialize Telemetry Collector
    telemetry_collector = TelemetryCollector(interval_seconds=config.agent.heartbeat_interval) # Use heartbeat interval for telemetry
    telemetry_collector_task = asyncio.create_task(telemetry_collector.start())
    logger.info("Telemetry Collector initialized and started.")



    if args.mode == "dry-run":
        logger.info("Dry-run mode: Configuration loaded successfully. Exiting.")
        return

    # --- AGT-001: Implement agent registration process ---
    # Perform registration *before* initializing transport if transport needs agent identity
    # Registration will fetch agent_id and signed_certificate_pem
    if not await register_agent_with_manager(agent_state, config, private_key_pem, public_key_pem, key_path, cert_path):
        if config.agent.mode == "collector-only":
            logger.warning("Agent registration failed, but proceeding in collector-only mode.")
            # In collector-only mode, we might proceed without a manager connection
            # Agent ID might be missing or default, handle this in collectors/transport if needed
            agent_state.agent_id = config.agent.id # Use configured ID as fallback
        else:
            logger.critical("Agent registration failed. Exiting.")
            sys.exit(1)
    # --- End AGT-001: Agent registration ---

    # 4. Initialize transport (Bus)
    transport = None
    try:
        # Pass agent_state to transport for mTLS client cert/key paths
        transport = await initialize_transport(config, agent_state, jwt_manager)
        await transport.connect() # Ensure connection is established
        agent_state.bus_connected = True
        logger.info(f"Transport initialized: {config.agent.bus.type}")
    except Exception as e:
        logger.critical(f"Failed to initialize or connect transport: {e}", exc_info=True)
        # Depending on criticality, we might exit or degrade
        if args.mode != "collector-only": # If not collector-only, transport is critical
            logger.critical("Cannot proceed without functional transport. Exiting.")
            sys.exit(1)
        else:
            logger.warning("Proceeding in collector-only mode without full transport connectivity.")
            agent_state.bus_connected = False


    # 5. Initialize Actions
    actions: Dict[str, Action] = {}
    for action_key, action_class in ACTION_CLASSES.items():
        actions[action_key] = action_class(logger=logger, config=config, adapter=agent_state.adapter) # Pass Pydantic model directly
        logger.debug(f"Initialized action handler: {action_key}")

    # 6. Initialize PluginLoader and load plugins
    loaded_plugins: Dict[str, Plugin] = {}
    if config.agent.plugins.enabled:
        plugin_dirs = [Path(p).resolve() for p in config.agent.plugins.paths]
        plugin_loader = PluginLoader(plugin_dirs, config.agent.plugins.allowed_permissions)
        loaded_plugins = plugin_loader.load_plugins()
        agent_state.plugins = loaded_plugins # Store loaded plugins in state
        logger.info(f"Loaded {len(loaded_plugins)} plugins.")

    # 7. Initialize and start Orchestrator
    orchestrator = Orchestrator(transport=transport, plugin_loader=plugin_loader)
    agent_state.orchestrator = orchestrator # Store orchestrator in agent_state
    orchestrator_task = asyncio.create_task(orchestrator.start())
    logger.info("Orchestrator started.")

    # 8. Run collectors (if not in forensics mode, they run continuously)
    if config.agent.mode in ["full", "collector-only", "osint"]:
        logger.debug(f"Preparing to run collectors. Found {len(config.agent.collectors)} configured collectors.")
        await run_collectors(agent_state, orchestrator) # Pass orchestrator instead of transport
    elif config.agent.mode == "forensics":
        # Forensics mode would typically involve one-shot data gathering then exit
        logger.info("Forensics mode: Performing one-shot data collection (not yet implemented).")
        pass # Implement one-shot collection logic here

    # --- Start Agent Health Monitor ---
    health_monitor = AgentHealthMonitor(
        agent_manager_url=str(config.agent.manager_url),
        heartbeat_interval=config.agent.heartbeat_interval, # Assuming a config value for interval
        jwt_manager=jwt_manager # Pass the JWTManager instance
    )
    health_monitor_task = asyncio.create_task(health_monitor.start())
    logger.info("AgentHealthMonitor started.")
    # --- End Agent Health Monitor ---

    # --- Start Self-Healing Controller ---
    from phantomnet_agent.self_healing_ai.self_healing_controller import SelfHealingController
    self_healing_controller = SelfHealingController(agent_dir=str(Path.cwd()))
    self_healing_controller_task = asyncio.create_task(self_healing_controller.start())
    logger.info("Self-Healing Controller started.")
    # --- End Self-Healing Controller ---

    # 9. Start local API (if enabled, and not collector-only/forensics where it might not be needed)
    api_task = None
    if config.agent.mode in ["full", "osint"] and config.agent.bus.type != "http": # HTTP bus is usually backend-facing
        try:
            api_task = asyncio.create_task(run_api(agent_state, args.api_host, args.api_port))
        except Exception as e:
            logger.error(f"Failed to start local API: {e}", exc_info=True)


    # 10. Enter main loop for commands (if not collector-only)
    main_loop_task = None
    if config.agent.mode in ["full", "osint"] and transport:
        # Pass orchestrator to main_loop so it can ingest commands
        main_loop_task = asyncio.create_task(main_loop(config, transport, actions, loaded_plugins, orchestrator))
    else:
        logger.info(f"Agent running in {config.agent.mode} mode. Not entering command reception loop.")
        # If no main loop, just keep other tasks (collectors, API) running
        # Need a way to keep event loop alive for collectors/API
        if api_task:
            await api_task # Keep API alive
        else:
            # If nothing else is running, just sleep indefinitely or until shutdown
            logger.info("Agent running in a background-only mode (collectors/API). Use Ctrl+C to exit.")
            try:
                while True:
                    await asyncio.sleep(3600) # Sleep for a long time
            except asyncio.CancelledError:
                pass
        
            try:
                # Wait for the main loop or API to finish, or for a shutdown signal
                if main_loop_task:
                    await main_loop_task
                elif api_task:
                    await api_task
                # Keep the event loop alive for log_forwarder and telemetry collector even if main_loop_task/api_task are None
                await log_forwarder_task # Await its completion if it ever stops, or it keeps the loop alive
                await telemetry_collector_task # Await its completion
            except asyncio.CancelledError:
                logger.info("Main execution cancelled.")
            finally:
                logger.info("Performing graceful shutdown of all components...")
                
                # Stop collectors
                for name, collector in agent_state.collectors.items():
                    if collector.running:
                        await collector.stop()
                        logger.info(f"Collector '{name}' stopped.")

                # Stop AgentHealthMonitor
                await health_monitor.stop()
                logger.info("AgentHealthMonitor stopped.")

                # Stop Orchestrator
                await orchestrator.stop()
                logger.info("Orchestrator stopped.")
        
                # Stop LogForwarder
                await log_forwarder_handler.stop()
                logger.info("Log forwarder stopped.")

                # Stop Telemetry Collector
                await telemetry_collector.stop()
                logger.info("Telemetry Collector stopped.")
        
                # Stop Self-Healing Controller
                await self_healing_controller.stop()
                logger.info("Self-Healing Controller stopped.")

                # Close transport
                if transport:
                    await transport.disconnect()
                    logger.info("Transport disconnected.")
        
                logger.info("PhantomNet Agent stopped.")
            
            
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent stopped by user (Ctrl+C).", file=sys.stderr)
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}", file=sys.stderr)
        sys.exit(1)
