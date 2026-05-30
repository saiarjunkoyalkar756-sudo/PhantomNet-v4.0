# simulate_load_attacks.py
# Automated High-Volume Threat Stress Test for PhantomNet v4.0
# Orchestrates 100 simulated attack campaigns with async execution and live status polling.

import asyncio
import httpx
import json
import time
import os
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000/api/v1/bas"
LOGS_DIR = "logs"
RESULTS_FILE = os.path.join(LOGS_DIR, "load_test_results.json")

os.makedirs(LOGS_DIR, exist_ok=True)

# 100 Attack Vectors mapped to fully native simulation types
ATTACKS_CONFIG = {
    "Low (Recon & Phishing)": {
        "count": 10,
        "type": "phishing",
        "targets": [f"ceo@company_target_{i:02d}.com" for i in range(1, 11)],
        "params": lambda i: {"subject": "Urgent account verification required", "recipient": f"ceo@company_target_{i:02d}.com"}
    },
    "Medium (Probes & SQLi)": {
        "count": 20,
        "type": "sqli",
        "targets": [f"user_portal_db_{i:02d}" for i in range(1, 21)],
        "params": lambda i: {"vector": "username_field", "payload": "admin' OR 1=1 --"}
    },
    "High (Exploitation & PE)": {
        "count": 30,
        "type": "privilege_escalation",
        "targets": [f"analytics_web_app_{i:02d}" for i in range(1, 31)],
        "params": lambda i: {"vector": "bypassuac", "payload": "bypassuac.exe"}
    },
    "Critical (Ransomware)": {
        "count": 20,
        "type": "ransomware",
        "targets": [f"prod_file_server_{i:02d}" for i in range(1, 21)],
        "params": lambda i: {"vector": "crypto_lock", "payload": "vssadmin delete shadows"}
    },
    "Advanced Critical (Cred Dump)": {
        "count": 10,
        "type": "credential_access",
        "targets": [f"prod_domain_controller_{i:02d}" for i in range(1, 11)],
        "params": lambda i: {"vector": "mimikatz", "payload": "sekurlsa::logonpasswords"}
    },
    "Most Logical Advanced (Lateral)": {
        "count": 5,
        "type": "lateral_movement",
        "targets": [f"dc_replica_{i:02d}" for i in range(1, 6)],
        "params": lambda i: {"vector": "psexec", "payload": "psexec.exe \\\\domain cmd.exe"}
    },
    "Blackhat Level (Exfiltration)": {
        "count": 5,
        "type": "exfiltration",
        "targets": [f"db_mirror_{i:02d}" for i in range(1, 6)],
        "params": lambda i: {"vector": "dns_tunnel", "payload": "DNS tunnel upload client.zip"}
    }
}

async def trigger_and_poll_simulation(client: httpx.AsyncClient, category: str, sim_type: str, target: str, params: dict) -> Dict[str, Any]:
    payload = {
        "simulation_type": sim_type,
        "target": target,
        "parameters": params
    }
    
    start_time = time.time()
    try:
        # 1. Trigger Simulation
        response = await client.post(f"{BASE_URL}/start_simulation", json=payload, timeout=10.0)
        
        if response.status_code == 200:
            res_json = response.json()
            sim_id = res_json.get("data", {}).get("simulation_id")
            if not sim_id:
                return {
                    "category": category, "type": sim_type, "target": target, "simulation_id": None,
                    "status": "failed", "score": 0.0, "blocked": False, "error": "No simulation ID returned", "latency_ms": int((time.time() - start_time) * 1000)
                }
            
            # 2. Poll status until complete (no longer 'running')
            status = "running"
            score = 0.0
            max_retries = 30
            retry_count = 0
            
            while status == "running" and retry_count < max_retries:
                await asyncio.sleep(1.0)
                res_check = await client.get(f"{BASE_URL}/simulation_results/{sim_id}", timeout=5.0)
                
                if res_check.status_code == 200:
                    res_check_json = res_check.json()
                    status = res_check_json.get("data", {}).get("status", "running")
                    score = res_check_json.get("data", {}).get("score", 0.0)
                elif res_check.status_code == 404:
                    status = "running"  # Background task is still running, keep polling
                else:
                    status = "failed"
                    break
                retry_count += 1
                
            duration = time.time() - start_time
            blocked = (status == "prevented")
            
            return {
                "category": category,
                "type": sim_type,
                "target": target,
                "simulation_id": sim_id,
                "status": status,
                "score": score,
                "blocked": blocked,
                "error": None if status != "failed" else "Check endpoint returned error",
                "latency_ms": int(duration * 1000)
            }
        else:
            return {
                "category": category,
                "type": sim_type,
                "target": target,
                "simulation_id": None,
                "status": "failed",
                "score": 0.0,
                "blocked": False,
                "error": f"Trigger API returned status code {response.status_code}",
                "latency_ms": int((time.time() - start_time) * 1000)
            }
    except Exception as e:
        return {
            "category": category,
            "type": sim_type,
            "target": target,
            "simulation_id": None,
            "status": "error",
            "score": 0.0,
            "blocked": False,
            "error": str(e),
            "latency_ms": int((time.time() - start_time) * 1000)
        }

async def main():
    print("==========================================================")
    print("PHANTOMNET v4.0 — HIGH-VOLUME 100+ THREAT STRESS TEST")
    print("==========================================================")
    print("[*] Launching 100 simulated attack campaigns asynchronously...")
    
    tasks = []
    async with httpx.AsyncClient() as client:
        # Build tasks for 100 attacks
        for category, config in ATTACKS_CONFIG.items():
            sim_type = config["type"]
            count = config["count"]
            
            for i in range(count):
                target = config["targets"][i]
                params = config["params"](i)
                tasks.append(trigger_and_poll_simulation(client, category, sim_type, target, params))
                
        print(f"[*] Queue initialized: {len(tasks)} attacks prepared.")
        print("[*] Flooding endpoint and polling async tasks to completion...")
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
    print("\n==========================================================")
    print("STRESS TEST CAMPAIGN COMPLETED")
    print(f"Total Execution Time: {total_time:.2f} seconds")
    print(f"Throughput: {len(tasks)/total_time:.2f} attacks/second")
    print("==========================================================")
    
    # Aggregation
    category_summary = {}
    total_blocked = 0
    total_detected = 0
    total_successful = 0
    
    for r in results:
        cat = r["category"]
        if cat not in category_summary:
            category_summary[cat] = {"total": 0, "prevented": 0, "detected": 0, "successful": 0}
            
        category_summary[cat]["total"] += 1
        status = r["status"]
        
        if status == "prevented":
            category_summary[cat]["prevented"] += 1
            total_blocked += 1
        elif status == "detected":
            category_summary[cat]["detected"] += 1
            total_detected += 1
        elif status == "successful":
            category_summary[cat]["successful"] += 1
            total_successful += 1
            
    # Print Dashboard
    print(f"\n{'THREAT TIER':<32} | {'TOTAL':<6} | {'BLOCKED':<8} | {'DETECTED':<8} | {'SUCCESSFUL':<10}")
    print("-" * 75)
    for cat, counts in category_summary.items():
        print(f"{cat:<32} | {counts['total']:<6} | {counts['prevented']:<8} | {counts['detected']:<8} | {counts['successful']:<10}")
        
    print("-" * 75)
    print(f"{'TOTAL AGGREGATED':<32} | {len(results):<6} | {total_blocked:<8} | {total_detected:<8} | {total_successful:<10}")
    print("==========================================================")
    
    prevention_rate = (total_blocked / len(results)) * 100
    detection_rate = ((total_blocked + total_detected) / len(results)) * 100
    
    print(f"[*] Platform Prevention Rate (Blocked): {prevention_rate:.1f}%")
    print(f"[*] Platform Overall Detection Rate: {detection_rate:.1f}%")
    print("==========================================================")
    
    # Save outcomes to JSON
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)
    print(f"[*] Bulk raw results successfully saved to {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
