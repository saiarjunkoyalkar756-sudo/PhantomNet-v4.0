# PhantomNet v4.0 — UPGRADE TO 10/10
# ═══════════════════════════════════════════════════════════════
# Repo: https://github.com/saiarjunkoyalkar756-sudo/PhantomNet-v4.0
# Current: 7.2/10 → Target: 10/10
# ═══════════════════════════════════════════════════════════════

You are a world-class senior software architect, cybersecurity
engineer, and DevOps expert.

Your mission is to upgrade PhantomNet v4.0 to a perfect 10/10
production-ready enterprise platform.

First clone the repo and read everything:
- PHANTOMNET_CONTEXT.md
- task.md
- docker-compose.yml
- .env.example
- All files in .github/workflows/
- All main.py and app.py in backend_api/
- phantomnet_agent/analyzers/rule_based_analyzer.py
- shared/settings.py
- blockchain_layer/
- phantomnet-website/

Understand the full architecture before making any changes.
Then work through every phase below completely.
Commit to git after completing each phase.

═══════════════════════════════════════════════════════════════
PHASE 1 — SECURITY: Bring to 10/10
═══════════════════════════════════════════════════════════════

1.1 Rate Limiting
Add rate limiting to every authentication endpoint across
all services. Limit login to 5 requests per minute per IP.
Limit registration to 3 per minute. Limit token refresh to
10 per minute. Block the IP automatically after 10 failed
attempts in 5 minutes. Store rate limit state in Redis so
it works across all service instances.

1.2 Input Validation
Add strict input validation to every public API endpoint
in all 28 services. Validate data types, lengths, formats,
and allowed characters. Reject any request with unexpected
fields. Return consistent 422 error responses with clear
messages. Never let raw user input reach the database or
Kafka without validation.

1.3 Security Headers
Add these HTTP security headers to every service response:
Strict-Transport-Security, Content-Security-Policy,
X-Frame-Options, X-Content-Type-Options, X-XSS-Protection,
Referrer-Policy, Permissions-Policy. Add a middleware that
applies all headers automatically to every response.

1.4 CORS Configuration
Fix CORS on all services. Only allow the frontend domain
and the gateway service. Never allow wildcard origins in
production. Different CORS rules for development vs
production using the ENVIRONMENT env variable.

1.5 SQL Injection Final Sweep
Scan every single database query across all 28 services.
Find any remaining f-string SQL or string concatenation
in queries. Replace every one with parameterized queries
or ORM methods. Add a test that verifies injection
payloads are rejected.

1.6 Secrets Management
Audit every file for any remaining hardcoded secrets,
API keys, passwords, or tokens. Move every single one to
environment variables. Add startup validation that checks
all required secrets are present and meet minimum
complexity requirements before any service starts.

1.7 JWT Hardening
Add JWT token expiry validation. Add token revocation
using a Redis blacklist. Add refresh token rotation so
old refresh tokens cannot be reused. Add device
fingerprinting to JWT claims. Reject tokens with
unexpected claims or missing required fields.

1.8 Dependency Security
Run safety check on all requirements.txt files.
Update every package with a known CVE to the latest
safe version. Add a pre-commit hook that blocks
commits adding vulnerable dependencies.

═══════════════════════════════════════════════════════════════
PHASE 2 — SERVICE CONNECTIVITY: Bring to 10/10
═══════════════════════════════════════════════════════════════

2.1 Kafka Topic Standardization
Create a single file shared/kafka_topics.py that defines
every Kafka topic name as a constant. Update every service
that produces or consumes Kafka messages to import topic
names from this file. Never use hardcoded topic name
strings anywhere in the codebase. Verify every producer
has at least one matching consumer.

2.2 Dead Letter Queues
Add a dead letter queue for every Kafka consumer.
If a message fails processing 3 times it goes to the
dead letter queue. Add a service that monitors dead
letter queues and creates alerts for failed messages.
Add a retry mechanism with exponential backoff.

2.3 Reconnect Logic
Add automatic reconnect with exponential backoff to
every Kafka consumer and producer. Add reconnect logic
to every database connection. Add reconnect logic to
every Redis connection. Services should never crash
permanently due to a temporary connection failure.
They should keep retrying until the dependency is back.

2.4 Service Discovery
Replace every hardcoded localhost URL with the proper
Docker service name. Audit docker-compose.yml to ensure
every service name matches what other services reference.
Add a startup check that verifies all required services
are reachable before the service starts accepting traffic.

2.5 Blockchain Connection
Connect the blockchain_layer to the audit_log_collector
service. Every security event that creates an alert
should write an immutable record to the blockchain.
Every SOAR action taken should be recorded. Verify
the ledger is actually writing and readable.

2.6 Enrichment Service Connection
Connect microservices/enrichment_service to the event
pipeline. It should consume normalized events from Kafka,
enrich them with threat intelligence data, and produce
enriched events back to a new Kafka topic. Connect the
AI behavioral engine to consume enriched events.

2.7 Event Flow Verification
Trace every event from agent ingestion to final storage.
Document every hop. Verify each hop works end to end.
Write an integration test that sends a test event and
verifies it appears in the database after flowing
through the entire pipeline.

═══════════════════════════════════════════════════════════════
PHASE 3 — PRODUCTION READINESS: Bring to 10/10
═══════════════════════════════════════════════════════════════

3.1 Graceful Shutdown
Add graceful shutdown handling to every service.
On SIGTERM, stop accepting new requests, finish
processing in-flight requests, flush Kafka producers,
close database connections cleanly, then exit.
Maximum shutdown time should be 30 seconds.

3.2 Circuit Breaker
Add a circuit breaker to every external service call.
If a dependency fails 5 times in 60 seconds, open the
circuit and return a fallback response instead of
waiting for timeout. Close the circuit again after
30 seconds if the dependency recovers. Log every
circuit state change as a warning.

3.3 Health Checks
Standardize health checks across all services.
Every service must have a /health endpoint that checks
its own database connection, Kafka connection, Redis
connection, and any critical dependencies. Return
a structured JSON response with the status of each
dependency. Docker healthchecks must use this endpoint.

3.4 Resource Limits
Add CPU and memory limits to every service in
docker-compose.yml. Set realistic limits based on
what each service actually needs. Add resource
reservations so services always have minimum resources.
Add alerts when any service exceeds 80% of its limit.

3.5 Logging Standards
Implement structured JSON logging in every service.
Every log line must include timestamp, service name,
log level, correlation ID, request ID, and message.
Never log passwords, tokens, or PII. Add log rotation
so logs do not fill the disk. Ship logs to a central
location using the Docker logging driver.

3.6 Metrics and Observability
Add Prometheus metrics to every service. Track request
count, request duration, error rate, Kafka consumer lag,
database query time, and active connections. Add a
Grafana dashboard that shows all services at a glance.
Add alerting rules for high error rates and slow queries.

3.7 Database Migrations
Create proper Alembic migration files for every database
schema change. Number them sequentially. Add a startup
check that verifies the database schema is at the correct
version before the service starts. Never auto-migrate in
production without a backup.

3.8 API Versioning
Add /api/v1/ prefix to every endpoint that does not
already have it. Plan for /api/v2/ without breaking v1.
Add API version to every response header. Add deprecation
warnings to any old endpoints that will be removed.

3.9 Error Response Standardization
Create a standard error response format used by every
service. Every error must include a code, message,
details, and request ID. Never expose stack traces
or internal error messages to API clients in production.
Log the full error internally but return a safe message.

3.10 Configuration Validation
Add startup validation to every service that checks
every required environment variable is present, meets
minimum security requirements, and can successfully
connect to its dependencies before accepting traffic.
Fail fast with a clear error message if anything is wrong.

═══════════════════════════════════════════════════════════════
PHASE 4 — CI/CD: Bring to 10/10
═══════════════════════════════════════════════════════════════

4.1 Complete CI Pipeline
Update .github/workflows/ci.yml to run on every push
and pull request. It must run linting with flake8,
type checking with mypy, security scanning with bandit,
dependency vulnerability check with safety, all unit
tests with pytest and coverage, Docker image builds
for all services, and a full integration test suite.
The pipeline must fail if coverage drops below 80%.

4.2 Complete CD Pipeline
Create .github/workflows/cd.yml for deployment.
On merge to main deploy to staging automatically.
Run smoke tests on staging. Require manual approval
to deploy to production. Tag Docker images with the
git SHA. Push images to Amazon ECR in ap-southeast-2.
Deploy to EC2 or ECS using the new images.

4.3 Automated Rollback
Add automatic rollback to the CD pipeline. If any
health check fails after deployment, automatically
roll back to the previous version. Send a notification
when a rollback happens. Keep the last 3 deployments
available for manual rollback.

4.4 Environment Promotion
Create three environments: development, staging,
production. Each has its own .env file, its own
database, its own secrets. Code flows from dev to
staging to production. No direct deploys to production
without passing staging.

4.5 Security Scanning in CI
Add a weekly security workflow that runs SAST with
bandit, dependency scanning with safety and pip-audit,
secret scanning with trufflehog, Docker image scanning
with trivy, and OWASP ZAP against the staging environment.
Create a GitHub issue automatically for any critical finding.

4.6 Performance Benchmarks in CI
Add a performance test job that runs on every merge
to main. Use locust or k6 to send 100 concurrent users
against the API for 60 seconds. Fail the pipeline if
average response time exceeds 500ms or error rate
exceeds 1%. Track performance trends over time.

4.7 Agent Build Pipeline
Create .github/workflows/agent-build.yml that builds
the agent for Linux x86_64, Linux arm64, Windows x86_64,
and Android Termux. Run platform-specific tests on each.
Create release artifacts and attach them to GitHub releases
automatically on version tags.

4.8 PR Quality Gates
Add branch protection rules to the main branch.
Require at least one code review approval. Require all
CI checks to pass. Require linear history. Require
the branch to be up to date with main. Block direct
pushes to main from anyone including the owner.

═══════════════════════════════════════════════════════════════
PHASE 5 — TEST COVERAGE: Bring to 10/10
═══════════════════════════════════════════════════════════════

5.1 Unit Tests for Every Service
Write unit tests for every function in every service
that has business logic. Every detection rule must have
a test that verifies it catches the attack it is meant
to catch. Every SOAR action must have a test that
verifies it executes correctly. Target 90% line coverage
per service.

5.2 Integration Tests with Docker
Write integration tests that start the full Docker stack
and test the complete event flow end to end. Send a
real event through the pipeline and verify it appears
in the database. Fire each attack type and verify it
creates an alert and blocks the IP. Test the compliance
reports contain correct data.

5.3 Next.js Portal Tests
Write tests for every page and API route in the
phantomnet-website portal. Test the admin portal
authentication. Test the blacklist management actually
updates the database. Test the real-time log streaming.
Test every API proxy route returns the correct data.

5.4 Blockchain Layer Tests
Write tests that verify the blockchain ledger actually
records transactions. Test that records cannot be
tampered with. Test that the audit trail is complete
for every security event. Test the query interface
returns correct history.

5.5 Agent Tests
Write tests for every collector module. Test the
network collector on Linux and Windows. Test the
process collector correctly identifies suspicious
processes. Test every detection rule with real
malicious payloads. Test the countermeasures actually
execute the correct system commands.

5.6 Security Tests
Write tests specifically designed to verify security
controls work. Test that SQL injection payloads are
rejected. Test that XSS payloads are sanitized.
Test that rate limiting actually blocks after the
limit is reached. Test that JWT tokens cannot be
forged. Test that blocked IPs cannot access any endpoint.

5.7 Performance Tests
Write load tests using locust or k6. Test the telemetry
ingestor can handle 10,000 events per second. Test the
gateway service can handle 1,000 concurrent connections.
Test the SOAR engine can process 100 alerts per second.
Document the maximum throughput of each service.

5.8 Chaos Engineering Tests
Write chaos tests that verify the system recovers from
failures. Kill the database and verify services reconnect
automatically. Kill Kafka and verify messages are not
lost. Kill a random service and verify the others
continue working. Kill the Redis cache and verify
services fall back gracefully.

═══════════════════════════════════════════════════════════════
PHASE 6 — CODE QUALITY: Bring to 10/10
═══════════════════════════════════════════════════════════════

6.1 Type Hints Everywhere
Add complete type hints to every function in every Python
file. Every parameter, every return value, every variable
assignment. Run mypy with strict mode and fix every error.
Add mypy to the CI pipeline to prevent regressions.

6.2 Docstrings on Everything
Add docstrings to every class, every function, every module.
Explain what it does, what the parameters are, what it
returns, and what exceptions it can raise. Use Google style
docstrings consistently across the entire codebase.

6.3 Remove All Dead Code
Find and remove every function that is never called.
Remove every import that is never used. Remove every
commented-out block of code. Remove every TODO that
is actually already done. Keep only what is needed.

6.4 Fix All Bare Except Clauses
Find every bare except clause in the codebase.
Replace every one with the specific exception type
it is meant to catch. If you do not know the exception
type, catch Exception and log the full traceback.
Never silently swallow exceptions in production code.

6.5 Consistent Error Handling
Audit every try/except block. Every exception must be
logged with enough context to debug the issue. Every
exception that affects the user must return a proper
error response. Never let an unhandled exception
return a 500 with a stack trace in production.

6.6 OpenAPI Documentation
Add complete OpenAPI documentation to every endpoint
in every FastAPI service. Every endpoint must have a
summary, description, request body schema, response
schemas for all status codes, and example values.
The /docs page on every service must be complete and
accurate.

6.7 Code Consistency
Run black formatter on all Python files and commit
the result. Run isort on all imports. Add pre-commit
hooks for black, isort, flake8, and mypy. Add these
to CI so the pipeline fails on formatting violations.
The entire codebase must have consistent style.

6.8 Dependency Cleanup
Audit every requirements.txt file across all services.
Remove packages that are imported but never actually used.
Pin every package to an exact version for reproducibility.
Split requirements into base, development, and production.
Add a comment explaining why each unusual package is needed.

═══════════════════════════════════════════════════════════════
PHASE 7 — NEXT.JS PORTAL: Bring to 10/10
═══════════════════════════════════════════════════════════════

7.1 Admin Portal Completion
Complete every page in the admin portal. The infrastructure
grid page must show real service health from the API.
The blacklist management page must read and write to the
real database. The BAS launcher must actually trigger
playbooks. The load averages must come from real metrics.
Nothing should show hardcoded or fake data.

7.2 User Shield Portal Completion
Complete the user portal. The endpoint posture score must
come from the real vulnerability management service.
The honeypot status must come from the real honeypot service.
The live telemetry log stream must use a real WebSocket
connection to the backend. Token rotation must call
the real auth endpoint.

7.3 Authentication and Authorization
Add proper authentication to the Next.js portal.
The admin portal must require an admin JWT token.
The user portal must require a user JWT token.
Add route protection using Next.js middleware.
Redirect unauthenticated users to login.
Add role-based access control for different admin functions.

7.4 Real-time Data
Add WebSocket connections for all live data in the portal.
Alerts should appear in real time without page refresh.
Service health should update every 30 seconds automatically.
The telemetry log stream should be a true live stream.
Add a connection status indicator so users know if the
real-time connection is active or reconnecting.

7.5 Mobile Responsiveness
Make every page in both portals fully responsive.
Test on mobile, tablet, and desktop screen sizes.
The SOC dashboard must be usable on a mobile device.
Add touch-friendly interactions for mobile users.

═══════════════════════════════════════════════════════════════
PHASE 8 — DOCUMENTATION: Maintain 10/10
═══════════════════════════════════════════════════════════════

8.1 Architecture Decision Records
Create a docs/adr/ folder. Write an ADR for every
major architectural decision. Why Kafka over RabbitMQ.
Why Neo4j for the attack graph. Why the blockchain
layer was added. Why FastAPI over Django. Each ADR
should explain the context, the decision, and the
consequences.

8.2 Runbook
Create a complete operations runbook at docs/runbook.md.
Cover how to deploy, how to roll back, how to scale
individual services, how to diagnose common issues,
how to rotate secrets, how to back up and restore
the database, and how to respond to a security incident.

8.3 API Reference
Generate complete API reference documentation for
all 28 services using the OpenAPI specs. Host it
at a single URL. Include authentication instructions,
rate limit information, error code reference, and
example requests and responses for every endpoint.

8.4 Developer Setup Guide
Write a complete developer setup guide that takes
someone from zero to a running local development
environment in under 30 minutes. Include every
prerequisite, every command, every expected output,
and how to verify each step worked correctly.

8.5 Security Documentation
Document the complete security model. How JWT auth
works. How Zero Trust is enforced. How SOAR responds
to each attack type. What data is encrypted at rest
and in transit. How to report a security vulnerability.
What the penetration test results were.

═══════════════════════════════════════════════════════════════
PHASE 9 — PERFORMANCE: Bring to 10/10
═══════════════════════════════════════════════════════════════

9.1 Database Query Optimization
Profile every database query in every service. Add
in
