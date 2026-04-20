import logging
import os
import subprocess
import yara
import json
try:
    from scapy.all import rdpcap, IP, TCP, UDP, DNS
except ImportError:
    pass

logger = logging.getLogger("dfir_toolkit")

def run_yara_scan(file_path: str, rules_path: str = None) -> dict:
    """
    Executes a real YARA scan using the yara-python engine.
    """
    logger.info(f"[DFIR TOOL] Compiling YARA rules from {rules_path} and scanning {file_path}")
    
    if not os.path.exists(file_path):
        return {"matches": [], "status": "error", "error_message": f"File {file_path} not found."}

    try:
        if rules_path and os.path.exists(rules_path):
            rules = yara.compile(filepath=rules_path)
        else:
            # Fallback: Create a dynamic quick-rule in memory for high entropy / bad strings
            default_rule = '''
            rule GenericSuspicious {
                strings:
                    $mz = { 4D 5A }
                    $s1 = "Invoke-Expression" nocase
                    $s2 = "ReflectiveLoader"
                    $s3 = "VirtualAlloc"
                condition:
                    ($mz at 0) and any of ($s*)
            }
            '''
            rules = yara.compile(source=default_rule)

        matches = rules.match(file_path)
        
        match_results = []
        for match in matches:
            match_results.append({
                "rule": match.rule,
                "tags": match.tags,
                "strings": [str(s) for s in match.strings]
            })
            
        status = "detected" if matches else "clean"
        return {"matches": match_results, "status": status}
    
    except Exception as e:
        logger.error(f"YARA Engine Error: {e}")
        return {"matches": [], "status": "error", "error_message": str(e)}


def analyze_memory_dump(dump_path: str) -> dict:
    """
    Uses Volatility 3 command-line utility to pull process trees.
    Falls back to raw byte-search if Volatility is missing.
    """
    logger.info(f"[DFIR TOOL] Real memory analysis initiated on {dump_path}.")
    if not os.path.exists(dump_path):
        return {"status": "error", "error_message": "Memory dump file missing."}

    # Attempt Volatility 3 execution
    try:
        vol_result = subprocess.run(
            ["vol", "-f", dump_path, "windows.pstree.PsTree"], 
            capture_output=True, text=True, timeout=60
        )
        if vol_result.returncode == 0:
            return {
                "compromised_processes": "Extracted via Volatility3",
                "vol_output_snippet": vol_result.stdout[:500],
                "status": "analyzed_volatility"
            }
    except FileNotFoundError:
        logger.warning("Volatility3 ('vol') not in PATH. Utilizing Raw Memory Hex Search Fallback.")

    # Fallback to pure python raw memory scan 
    # Warning: Very memory intensive, we scan in chunks.
    suspicious_patterns = [b"mimikatz", b"sekurlsa::logonpasswords", b"lsass.exe", b"cobaltstrike"]
    findings = []
    
    try:
        with open(dump_path, 'rb') as f:
            chunk = f.read(1024 * 1024 * 10) # 10 MB chunk reading
            while chunk:
                for pattern in suspicious_patterns:
                    if pattern in chunk:
                        findings.append(f"Memory string found: {pattern.decode('utf-8')}")
                chunk = f.read(1024 * 1024 * 10)
                
        return {
            "compromised_processes": list(set(findings)),
            "malicious_injections": len(findings),
            "status": "raw_scanned" if findings else "clean"
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def analyze_pcap(pcap_path: str) -> dict:
    """
    Uses Scapy to parse PCAP files and extract anomalous layer 4 and DNS traffic.
    """
    logger.info(f"[DFIR TOOL] Real PCAP parsing initiated for {pcap_path}.")
    if not os.path.exists(pcap_path):
        return {"status": "error", "error_message": "PCAP file not found."}

    suspicious_dns = set()
    anomalous_connections = 0

    try:
        packets = rdpcap(pcap_path)
        for pkt in packets:
            if pkt.haslayer(IP):
                # Simple large payload anomaly
                if len(pkt) > 5000: 
                    anomalous_connections += 1
                
                # Extract DNS queries
                if pkt.haslayer(DNS) and pkt.getlayer(DNS).qr == 0:
                    query_name = pkt.getlayer(DNS).qd.qname
                    if query_name:
                        suspicious_dns.add(query_name.decode("utf-8"))
                        
        # Basic heuristic
        if len(suspicious_dns) > 50:
            status = "detected_dga_behavior"
        elif anomalous_connections > 10:
            status = "detected_exfiltration"
        else:
            status = "clean"
            
        return {
            "anomalous_connections": anomalous_connections,
            "suspicious_dns_queries": list(suspicious_dns)[:10], # Top 10
            "status": status,
        }
    except Exception as e:
        logger.error(f"Error parsing PCAP: {e}")
        return {"status": "error", "error_message": str(e)}


def reconstruct_timeline(event_logs_path: str) -> dict:
    """
    Parses directory of raw log files to construct an actionable forensic timeline.
    """
    logger.info(f"[DFIR TOOL] Timeline reconstruction parsing: {event_logs_path}.")
    if not os.path.isdir(event_logs_path):
        return {"status": "error", "error_message": "Log directory not found."}

    critical_events = []
    total_events = 0

    try:
        for filename in os.listdir(event_logs_path):
            file_path = os.path.join(event_logs_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, "r", errors='ignore') as f:
                    for line in f:
                        total_events += 1
                        # Basic keyword matching for critical events
                        lower_line = line.lower()
                        if any(k in lower_line for k in ["failed login", "error", "critical", "unauthorized", "bypass"]):
                            critical_events.append(line.strip()[:100])
                            
        return {
            "events_count": total_events,
            "critical_events": len(critical_events),
            "critical_samples": critical_events[:5], # Return first 5 criticals
            "timeline_generated": True,
            "status": "completed",
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
