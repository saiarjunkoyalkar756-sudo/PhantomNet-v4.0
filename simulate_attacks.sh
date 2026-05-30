#!/bin/bash
# simulate_attacks.sh
# Automated 3-Phase simulated attack execution against PhantomNet v4.0

set -e

LOGS_DIR="logs"
mkdir -p "$LOGS_DIR"

echo "=========================================================="
echo "PHANTOMNET v4.0 — 3-PHASE SIMULATED ATTACK GRID"
echo "=========================================================="

# --------------------------------------------------------
# PHASE 1: Recon & Initial Access (SQL Injection Simulation)
# --------------------------------------------------------
echo -e "\n[+] PHASE 1: Triggering SQL Injection Attack Simulation..."
curl -s -X POST http://localhost:8000/api/v1/bas/start_simulation \
  -H "Content-Type: application/json" \
  -d '{
    "simulation_type": "sqli",
    "target": "prod_db_server_01",
    "parameters": {
      "injection_vector": "username",
      "payload": "admin'\'' OR '\''1'\''='\''1"
    }
  }' > "$LOGS_DIR/attack_phase_1.log"

echo "[*] Phase 1 Response saved to $LOGS_DIR/attack_phase_1.log:"
cat "$LOGS_DIR/attack_phase_1.log"
sleep 2

# --------------------------------------------------------
# PHASE 2: Privilege Escalation & Execution (SOAR Ransomware Playbook)
# --------------------------------------------------------
echo -e "\n[+] PHASE 2: Triggering Automated SOAR Ransomware Containment Playbook..."
curl -s -X POST "http://localhost:8000/api/v1/soar/api/soar/playbooks/Ransomware%20Detected%20Playbook/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "prod_web_server_01",
    "source_ip": "192.168.4.15",
    "process_name": "encryptor.exe",
    "alert_id": "ALERT-RANSOMWARE-998"
  }' > "$LOGS_DIR/attack_phase_2.log"

echo "[*] Phase 2 Response saved to $LOGS_DIR/attack_phase_2.log:"
cat "$LOGS_DIR/attack_phase_2.log"
sleep 2

# --------------------------------------------------------
# PHASE 3: Forensic Artifact Evidence Collection
# --------------------------------------------------------
echo -e "\n[+] PHASE 3: Triggering Forensic Evidence Collection on Compromised Server..."
curl -s -X POST http://localhost:8000/api/v1/forensics/evidence/collect/ \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "prod_web_server_01",
    "job_id": "JOB-FORENSICS-8839-2A",
    "artifact_types": ["memory_dump", "system_logs", "mft.dat"],
    "collection_parameters": {
      "pcap_seconds": 60,
      "log_sources": ["auth.log", "syslog"]
    }
  }' > "$LOGS_DIR/attack_phase_3.log"

echo "[*] Phase 3 Response saved to $LOGS_DIR/attack_phase_3.log:"
cat "$LOGS_DIR/attack_phase_3.log"
sleep 2

echo -e "\n=========================================================="
echo "ATTACK PHASES COMPLETED SUCCESSFULY"
echo "=========================================================="

echo -e "\n[+] Verifying Internal Rotating Log Files in Logs Folder:"
echo "----------------------------------------------------------"
for logfile in "$LOGS_DIR"/*.log; do
  echo "[*] File: $logfile (Size: $(wc -c < "$logfile") bytes, Lines: $(wc -l < "$logfile"))"
done
echo "=========================================================="
