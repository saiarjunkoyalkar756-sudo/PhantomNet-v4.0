from .countermeasures import block_ip

def trigger_playbook(alert):
    if alert.get("rule_name") == "Network Anomaly - Port Scan":
        source_ip = alert.get("details", {}).get("source_ip")
        if source_ip:
            block_ip(source_ip)
