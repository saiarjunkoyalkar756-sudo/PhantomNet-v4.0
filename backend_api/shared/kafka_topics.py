# backend_api/shared/kafka_topics.py

TOPICS = {
    "RAW_TELEMETRY":     "phantomnet.raw_telemetry",
    "NORMALIZED_EVENTS": "phantomnet.normalized_events",
    "ALERTS":            "phantomnet.alerts",
    "COMMANDS":          "phantomnet.commands",
    "THREAT_INTEL":      "phantomnet.threat_intel",
    "FORENSICS_JOBS":    "phantomnet.forensics_jobs",
    "COMPLIANCE_EVENTS": "phantomnet.compliance_events",
}
