# PhantomNet v4.0 — CLEANUP, CONSOLIDATION & FRONTEND REWRITE
# ═══════════════════════════════════════════════════════════════
# Repo: https://github.com/saiarjunkoyalkar756-sudo/PhantomNet-v4.0
# Task: Remove clutter, consolidate everything, rewrite frontend
# ═══════════════════════════════════════════════════════════════

You are a senior software architect and full-stack engineer.
Your job is to clean up, consolidate, and rewrite PhantomNet v4.0
from a cluttered 1/10 frontend to a production-grade 10/10 SOC
dashboard platform.

Start by running these commands to understand what exists:
  cd PhantomNet-v4.0
  ls -la
  find . -name "*.md" | sort
  find . -name "*.py" | grep -v __pycache__ | sort
  find . -name "*.sh" | sort
  find . -name "Dockerfile*" | sort
  cat docker-compose.yml
  cat PHANTOMNET_CONTEXT.md

Understand EVERYTHING before touching anything.
Never delete anything without documenting why.
Commit after every phase.

═══════════════════════════════════════════════════════════════
PHASE 1 — AUDIT EVERY FOLDER AND FILE
═══════════════════════════════════════════════════════════════

Go through every single folder and file at root level.
For each one answer these three questions:
  - Is this actively used by any running service?
  - Is this imported or referenced anywhere in the code?
  - Would the project break if this was removed?

Audit every folder:
  PhantomNet-v3.0/     → Is v3 code ever imported by v4?
  DOCS/                → Is this different from docs/?
  docs/                → What is actually in here?
  features/            → Are these implemented or just plans?
  files/               → What systemd files are here?
  logs/                → Are real logs being written here?
  microservices/       → Is enrichment_service connected?
  mitre_data           → Is this file used by any service?
  phantomnet-cli       → Is this CLI tool working?
  phantomnet-website/  → Is this connected to the backend?
  plugins/             → Are any plugins implemented?
  website/             → Is this the same as phantomnet-website?
  blockchain_layer/    → Is this connected to any service?
  PhantomNet-v3.0/     → Is any v3 code still needed?
  .antigravitycli/     → What is this?
  .kiro/               → What is this?
  .claude/             → What is this?

Audit every root-level .md file:
  README.md            → KEEP - essential
  CHANGELOG.md         → KEEP - essential
  CLAUDE.md            → Is this needed for Claude AI agent?
  AGENTS.md            → Is this needed for AI agents?
  CONTRIBUTING.md      → KEEP - essential
  CODE_OF_CONDUCT.md   → KEEP - essential
  SECURITY.md          → KEEP - essential
  SUPPORT.md           → Review - may keep
  RELEASE_NOTES_v2.0.md → Is v2 release notes needed in v4?
  deployment_notes.md  → Merge into README or docs/
  implement.md         → Is this a plan or done work?
  testing.md           → Merge into docs/
  usage.md             → Merge into README
  task.md              → Is this still active?

Audit every root-level script:
  run_all.py           → Does this actually work?
  run_backend.sh       → Does this actually work?
  run_phantomnet.sh    → Does this actually work?
  run_manual.ps1       → Does this actually work?
  setup-nix.sh         → Does this actually work?
  install_agent.sh     → Does this actually work?
  install_agent.ps1    → Does this actually work?
  install_backend.sh   → Does this actually work?
  install_linux.sh     → Does this actually work?
  install_windows.ps1  → Does this actually work?
  Start-PhantomNet.ps1 → Does this actually work?
  Stop-PhantomNet.ps1  → Does this actually work?
  stop_grid.ps1        → Does this actually work?
  phantomnet-cli       → Does this actually work?

Audit every root-level Dockerfile:
  Dockerfile.backend              → Which service uses this?
  Dockerfile.event_stream_processor → Which service uses this?
  Dockerfile.orchestrator         → Which service uses this?
  Dockerfile.policy_engine        → Which service uses this?
  Dockerfile.pyinstaller          → Which service uses this?

Create a file called AUDIT_RESULTS.md that lists:
  - Every folder with KEEP / DELETE / MERGE decision
  - Every .md file with KEEP / DELETE / MERGE decision
  - Every script with KEEP / FIX / DELETE decision
  - Every Dockerfile with KEEP / MERGE / DELETE decision
  - Reason for every decision

Show me AUDIT_RESULTS.md before doing anything else.

═══════════════════════════════════════════════════════════════
PHASE 2 — REMOVE ALL CLUTTER
═══════════════════════════════════════════════════════════════

After audit is reviewed and approved, clean up:

2.1 Remove Duplicate and Obsolete Folders
  Remove PhantomNet-v3.0/ completely unless any v4 service
  imports from it. If anything imports from it, move only
  those specific files to the correct v4 location first.

  Remove DOCS/ if it is a duplicate of docs/
  If they have different content, merge them into docs/

  Remove website/ if it is a duplicate of phantomnet-website/
  If they have different content, merge the useful parts first

  Remove logs/ from the repository - logs should never be
  committed to git. Add logs/ to .gitignore instead.

  Remove features/ if these are just planning documents
  that describe features already implemented. If they
  describe unimplemented features, move them to docs/roadmap.md

2.2 Remove Unwanted .md Files
  Remove RELEASE_NOTES_v2.0.md - irrelevant in v4 repo
  Remove deployment_notes.md - merge content into docs/deployment.md
  Remove implement.md - merge content into docs/architecture.md
  Remove testing.md - merge content into docs/testing.md
  Remove usage.md - merge key content into README.md then delete
  Remove task.md - move active tasks to GitHub Issues instead

  Keep these .md files:
  README.md, CHANGELOG.md, CONTRIBUTING.md,
  CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md,
  CLAUDE.md (if needed for Claude agent), AGENTS.md

2.3 Consolidate Duplicate Scripts
  There are too many install and run scripts that likely
  do overlapping things. Consolidate them:

  Keep install_linux.sh as the single Linux installer
  Keep install_windows.ps1 as the single Windows installer
  Remove install_agent.sh if install_linux.sh covers it
  Remove install_backend.sh if docker compose covers it
  Remove setup-nix.sh if install_linux.sh covers it

  Keep run_phantomnet.sh as the single run script
  Remove run_backend.sh if run_phantomnet.sh covers it
  Remove run_all.py if docker compose covers it
  Remove run_manual.ps1 if docker compose covers it

  Keep Start-PhantomNet.ps1 and Stop-PhantomNet.ps1
  Remove stop_grid.ps1 if Stop-PhantomNet.ps1 covers it

2.4 Consolidate Dockerfiles
  Move all root-level Dockerfiles into infra/docker/
  Update docker-compose.yml to reference new paths
  Remove any Dockerfile that no service actually uses

2.5 Clean Up .gitignore
  Add these to .gitignore if not already there:
  logs/, *.log, __pycache__/, node_modules/,
  .env, *.pem, *.key, *.pyc, dist/, build/,
  .next/, .venv/, venv/, .pytest_cache/

2.6 Archive AI Agent Config Files
  Move .antigravitycli/, .kiro/, .claude/ into a folder
  called .ai-agents/ to keep them organized and out of
  the way. Update any references to their new paths.

After cleanup commit with message:
  "Phase 2: Remove clutter - deleted N files, merged M docs"

═══════════════════════════════════════════════════════════════
PHASE 3 — CONSOLIDATE ALL FEATURES INTO MAIN BACKEND
═══════════════════════════════════════════════════════════════

3.1 Audit What Features Exist But Are Not Integrated

Check every folder for features that exist in isolation
but are not connected to the main backend:

  blockchain_layer/
  → Is it writing audit records when alerts fire?
  → Is it called from audit_log_collector?
  → If not, integrate it now.

  microservices/enrichment_service/
  → Is it consuming events from Kafka?
  → Is it enriching events with threat intel?
  → If not, connect it to the normalized_events topic.

  phantomnet_core/
  → What does this contain that backend_api does not?
  → Are there duplicate implementations?
  → Merge unique functionality into backend_api/shared/

  plugins/
  → Are any plugins implemented end to end?
  → Is there a plugin loader in the main backend?
  → Either implement the plugin system fully or remove it.

  mitre_data
  → Is this file being read by mitre_attack_mapper?
  → If not, connect it.

  phantomnet-cli
  → Does this CLI work against the running backend?
  → If not, fix it or remove it.

3.2 Create a Single Backend Entry Point

Create a file called main.py at the project root that:
  - Imports and registers all service routers
  - Starts all background workers
  - Initializes all database connections
  - Starts all Kafka consumers
  - Runs health checks on all dependencies
  - Provides a single unified API on one port
  - Can be used for development without Docker

This is NOT a replacement for the microservices architecture.
It is a convenience entry point for development and testing.

3.3 Standardize Service Structure

Every service in backend_api/ must have the same structure:
  service_name/
    __init__.py
    main.py        → FastAPI app with all routes
    models.py      → Pydantic and database models
    database.py    → Database operations
    service.py     → Business logic
    tests/         → Service-specific tests
    requirements.txt → Service dependencies
    Dockerfile     → Service container

For any service missing these files, create them.
For any service that has them with different names, rename them.

3.4 Fix All Disconnected Services

Go through each service and verify it connects properly:
  → Is it in docker-compose.yml?
  → Does it have a healthcheck?
  → Does it depend_on the right services?
  → Are its environment variables in .env.example?
  → Does it handle startup failures gracefully?

For any service that fails any of these checks, fix it.

3.5 Update docker-compose.yml

After cleanup and consolidation, rewrite docker-compose.yml
to be clean and complete. Every active service gets an entry.
Removed services get removed from docker-compose. All paths
reference correct locations after the folder cleanup.
Add a minimal profile that runs only core services for
development on machines with less than 8GB RAM.

═══════════════════════════════════════════════════════════════
PHASE 4 — REWRITE FRONTEND SOC DASHBOARD FROM SCRATCH
═══════════════════════════════════════════════════════════════

The current dashboard_frontend is rated 1/10.
Rewrite it completely. Do not salvage the old code.
Keep the folder structure, delete the src/ contents,
and rebuild with a professional SOC dashboard design.

4.1 Design Requirements

The new dashboard must look and feel like a
professional enterprise SOC platform. Think of how
Splunk, Elastic Security, Microsoft Sentinel, or
Palo Alto Cortex XDR dashboards look. Dark theme
with high contrast. Data-dense but readable. Every
panel shows real data from the backend API.

4.2 Required Pages

MAIN SOC DASHBOARD (/)
  Real-time alert feed updating without page refresh
  Total events ingested today with trend line
  Active alerts by severity with counts
  Top 10 attack types in last 24 hours
  Blocked IPs count with recent blocks list
  Services health status grid showing all 28 services
  Geographic map showing attack source locations
  Alert severity chart over time (last 7 days)
  SOAR actions taken count with recent actions list
  Mean time to detect and mean time to respond metrics

ALERTS PAGE (/alerts)
  Full alert table with pagination
  Filter by severity, attack type, date range, source IP
  Search alerts by any field
  Click any alert to see full details panel
  Alert details show full payload, attribution, threat score
  Mark alert as investigated or false positive
  Bulk actions to close multiple alerts at once
  Export alerts to CSV

THREATS PAGE (/threats)
  Live attack map showing blocked attacks in real time
  Attack type breakdown with drill-down charts
  Top attacker IPs with geolocation and reputation
  MITRE ATT&CK matrix showing which techniques detected
  Threat timeline showing attack progression
  Attribution clusters showing threat actor groups

SOAR PAGE (/soar)
  All active playbooks with enable/disable toggle
  Playbook execution log showing every action taken
  Blocked IP list with ability to unblock
  Isolated agents list with ability to reconnect
  Open tickets with status and severity
  SOAR response time metrics
  Manual trigger for any playbook with target input

ASSETS PAGE (/assets)
  All registered agents with status (online/offline)
  Asset details showing OS, version, last seen, risk score
  Vulnerability scan results per asset
  CVE list with severity, patch status, and recommendation
  Risk score trend over time per asset
  Launch vulnerability scan button per asset

FORENSICS PAGE (/forensics)
  Active forensic jobs with status and progress
  Completed timeline view with event list
  Evidence artifacts list with download links
  Timeline visualization showing attack progression
  Filter by asset, date range, event type
  Export timeline to PDF report

COMPLIANCE PAGE (/compliance)
  ISO 27001 score and finding list
  SOC 2 score and finding list
  PCI DSS score and finding list
  GDPR score and finding list
  Overall compliance score with trend
  Non-compliant findings with remediation steps
  Generate and download compliance report button
  Last audit date and next audit date

NETWORK PAGE (/network)
  Attack graph visualization using the Neo4j data
  Network topology showing all known assets
  Attack path highlighting showing critical paths
  Lateral movement detection alerts
  Network segmentation violations
  Click any node to see its connections and alerts

SETTINGS PAGE (/settings)
  Manage API keys and integrations
  Configure alert thresholds
  Manage user accounts and roles
  Configure notification channels
  System health and version information
  Backup and restore configuration

4.3 Technical Requirements

Use the exact same tech stack already in package.json
which is React 19, Vite, and Tailwind CSS.

Every page must fetch real data from the backend API.
Use the API base URL from environment variable
VITE_API_BASE_URL defaulting to http://localhost:8001

Every page that shows live data must auto-refresh
using WebSocket or polling every 30 seconds.

Add a connection status indicator in the header
showing whether the backend is reachable.

Add loading states for every data fetch.
Add error states when API calls fail.
Add empty states when there is no data yet.

The dashboard must be responsive and work on
screens from 1280px wide upward. SOC analysts
use large monitors so optimize for that.

Add keyboard shortcuts for common actions.
Escape to close modals. Ctrl+K for search.
R to refresh current page data.

4.4 Component Architecture

Create these reusable components:
  StatCard        → Single metric with trend indicator
  AlertTable      → Reusable alert listing with filters
  SeverityBadge   → Color coded severity label
  ServiceStatus   → Green/red service health dot
  TimelineView    → Chronological event display
  AttackTypeChart → Bar chart of attack types
  ThreatScoreBar  → Visual threat score 0-100
  LiveFeed        → Auto-updating list of recent items
  NetworkGraph    → Interactive attack graph
  ComplianceGauge → Circular gauge for compliance score

4.5 API Integration

Create a src/api/ folder with one file per backend service:
  alerts.js        → GET /api/v1/alerts, filter, mark
  soar.js          → GET actions, POST unblock, trigger
  assets.js        → GET agents, launch scan
  forensics.js     → POST timeline, GET jobs
  compliance.js    → GET all standards
  threats.js       → GET dashboard, attack types
  network.js       → GET attack graph, topology
  health.js        → GET /health all services

Every API call must handle loading, error, and success states.
Add request caching so the same data is not fetched twice
in the same minute. Add retry logic for failed requests.

4.6 Authentication

Add a login page that calls the gateway auth endpoint.
Store the JWT token in memory not localStorage.
Add the token to every API request header.
Redirect to login when token expires.
Add a session timeout warning 5 minutes before expiry.

4.7 Real-time Updates

Use WebSocket connection to the backend for:
  Live alert feed on the main dashboard
  SOAR action notifications
  Service health status changes
  New blocked IP notifications

Fall back to polling every 30 seconds if WebSocket
connection fails. Show a warning banner when using
polling instead of WebSocket.

═══════════════════════════════════════════════════════════════
PHASE 5 — REWRITE PHANTOMNET-WEBSITE PORTAL
═══════════════════════════════════════════════════════════════

The phantomnet-website has an Admin Portal and User Shield
Portal. These also need to be properly connected to the
real backend APIs.

5.1 Admin Portal (/admin)
  Connect the infrastructure grid to the real health endpoint
  Connect blacklist management to the real database
  Connect BAS launcher to the real SOAR playbooks
  Connect load averages to real Prometheus metrics
  Every admin action must require admin JWT token
  Add audit log showing every admin action taken

5.2 User Shield Portal (/user)
  Connect posture score to real vulnerability management API
  Connect honeypot status to real honeypot service
  Connect telemetry stream to real WebSocket endpoint
  Connect token rotation to real auth endpoint
  Every user action must require user JWT token

5.3 Marketing Pages
  Ensure the marketing pages are fast and load correctly
  Remove any broken links or placeholder content
  Ensure contact forms are working or clearly disabled

═══════════════════════════════════════════════════════════════
PHASE 6 — VERIFY EVERYTHING WORKS TOGETHER
═══════════════════════════════════════════════════════════════

6.1 Start the Full Stack
  Run docker compose up and verify every service starts
  Check every service health endpoint responds
  Check the database schema is created correctly
  Check Kafka topics are created

6.2 Test the Dashboard
  Open http://localhost:3000 and verify it loads
  Verify the health status grid shows all services
  Send a test attack and verify it appears in alert feed
  Verify SOAR actions appear in the SOAR page
  Verify compliance scores show correct data
  Verify the attack graph shows nodes

6.3 Test the Portals
  Open http://localhost:3001 and verify it loads
  Log in to admin portal and verify all pages work
  Log in to user portal and verify all pages work

6.4 Run All Tests
  Run the full test suite and fix anything that fails
  Verify frontend builds without errors
  Verify no TypeScript or ESLint errors
  Verify all API integrations return correct data

6.5 Final Commit
  Commit all changes with clear message
  Push to main branch
  Verify CI pipeline passes
  Update README with new structure and setup instructions

═══════════════════════════════════════════════════════════════
RULES
═══════════════════════════════════════════════════════════════

Never delete anything without documenting it in AUDIT_RESULTS.md
Never break working backend services while cleaning up
Always show what changed and why before making changes
Always commit after each phase with a clear message
Always test that things still work after each cleanup step
If unsure whether to delete something, keep it and flag it
The backend services must keep working throughout all phases
The new dashboard must show real data not fake placeholder data

═══════════════════════════════════════════════════════════════
OUTPUT AFTER ALL PHASES
═══════════════════════════════════════════════════════════════

Provide these files:

AUDIT_RESULTS.md
  Every file and folder with keep/delete/merge decision

CLEANUP_REPORT.md
  Every file removed with reason
  Every file merged with destination
  Final
