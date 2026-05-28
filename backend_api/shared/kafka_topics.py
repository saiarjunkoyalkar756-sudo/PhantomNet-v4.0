# backend_api/shared/kafka_topics.py
"""
Centralized Kafka Topic Constants for PhantomNet Microservices.
Ensures zero hardcoded strings and unified topic structures.
"""

RAW_TELEMETRY = "phantomnet.raw_telemetry"
NORMALIZED_EVENTS = "phantomnet.normalized_events"
ALERTS = "phantomnet.alerts"
COMMANDS = "phantomnet.commands"
THREAT_INTEL = "phantomnet.threat_intel"
FORENSICS_JOBS = "phantomnet.forensics_jobs"
COMPLIANCE_EVENTS = "phantomnet.compliance_events"

# Backward compatibility map
TOPICS = {
    "RAW_TELEMETRY": RAW_TELEMETRY,
    "NORMALIZED_EVENTS": NORMALIZED_EVENTS,
    "ALERTS": ALERTS,
    "COMMANDS": COMMANDS,
    "THREAT_INTEL": THREAT_INTEL,
    "FORENSICS_JOBS": FORENSICS_JOBS,
    "COMPLIANCE_EVENTS": COMPLIANCE_EVENTS,
}
