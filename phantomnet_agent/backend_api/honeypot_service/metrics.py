# backend_api/honeypot_service/metrics.py
from prometheus_client import Counter, Gauge

# Define Prometheus metrics
honeypot_sessions_total = Counter(
    'honeypot_sessions_total',
    'Total number of honeypot sessions initiated.',
    ['honeypot_id', 'honeypot_type']
)

honeypot_events_total = Counter(
    'honeypot_events_total',
    'Total number of events captured by honeypots.',
    ['honeypot_id', 'honeypot_type', 'event_type']
)

honeypot_errors_total = Counter(
    'honeypot_errors_total',
    'Total number of errors encountered by honeypots.',
    ['honeypot_id', 'honeypot_type', 'error_type']
)

honeypot_active_instances = Gauge(
    'honeypot_active_instances',
    'Number of active honeypot instances.',
    ['honeypot_type']
)
