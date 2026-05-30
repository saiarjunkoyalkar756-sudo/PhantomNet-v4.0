# simulate_comprehensive_attacks.py
# Automated Enterprise Security Validation Suite for PhantomNet v4.0
# Orchestrates 130 distinct attack scenarios across 11 threat categories.

import asyncio
import httpx
import json
import time
import os
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000/api/v1/bas"
LOGS_DIR = "logs"
RESULTS_FILE = os.path.join(LOGS_DIR, "comprehensive_test_results.json")

os.makedirs(LOGS_DIR, exist_ok=True)

# 130 Attack Scenarios organized by exact requested categories and mapped to backend BAS modules
ATTACK_CATEGORIES = {
    "Low Severity (Recon/Passive)": {
        "type": "phishing",
        "scenarios": [
            "Open Port Enumeration", "DNS Enumeration", "WHOIS Reconnaissance", 
            "Subdomain Discovery", "Email Harvesting", "Employee Enumeration", 
            "Social Media Recon", "Technology Fingerprinting", "Service Banner Grabbing", 
            "Website Crawling", "Metadata Collection", "Public Repository Scraping", 
            "Search Engine Dorking", "SSL Certificate Enumeration", "Passive DNS Collection"
        ]
    },
    "Medium Severity (Probes/Access)": {
        "type": "sqli",
        "scenarios": [
            "Password Spraying", "Credential Stuffing", "Brute Force Login Attempt", 
            "Spear Phishing", "Attachment-Based Phishing", "Link-Based Phishing", 
            "MFA Fatigue Attack", "Session Hijacking Attempt", "Web Directory Traversal", 
            "SQL Injection Attempt", "Cross-Site Scripting Attempt", "CSRF Attempt", 
            "File Upload Abuse", "API Abuse Attempt", "Unauthorized Access Attempt"
        ]
    },
    "High Severity (Exploitation/Escalation)": {
        "type": "privilege_escalation",
        "scenarios": [
            "Privilege Escalation", "UAC Bypass Simulation", "Service Account Abuse", 
            "Scheduled Task Persistence", "Registry Persistence", "Startup Folder Persistence", 
            "Credential Dumping", "Pass-the-Hash", "Pass-the-Ticket", "Kerberoasting", 
            "AS-REP Roasting", "Remote Service Abuse", "SMB Lateral Movement", 
            "RDP Lateral Movement", "Internal Reconnaissance"
        ]
    },
    "Advanced (Execution/Cloud)": {
        "type": "exfiltration",
        "scenarios": [
            "DNS Tunneling", "Data Exfiltration", "Cloud Credential Theft", 
            "OAuth Token Abuse", "Cloud Privilege Escalation", "Kubernetes Reconnaissance", 
            "Container Escape Attempt", "Web Shell Deployment", "Command and Control Beaconing", 
            "Living Off The Land Activity", "WMI Execution Activity", "PowerShell Abuse", 
            "Remote Code Execution Simulation", "Supply Chain Compromise", "Insider Data Theft"
        ]
    },
    "Advanced Critical (Active Directory)": {
        "type": "credential_access",
        "scenarios": [
            "Domain Controller Recon", "Active Directory Enumeration", "Golden Ticket Simulation", 
            "Silver Ticket Simulation", "DCSync Simulation", "LSASS Memory Access", 
            "Domain Admin Impersonation", "Group Policy Abuse", "Trust Relationship Abuse", 
            "Enterprise Admin Escalation"
        ]
    },
    "Chain Attacks": {
        "type": "lateral_movement",
        "scenarios": [
            "Recon \u2192 Phishing Chain", "Phishing \u2192 Credential Theft Chain", 
            "Credential Theft \u2192 VPN Access Chain", "VPN Access \u2192 Lateral Movement Chain", 
            "Lateral Movement \u2192 Domain Takeover Chain", "SQLi \u2192 Data Exfiltration Chain", 
            "Web Shell \u2192 Persistence Chain", "Persistence \u2192 Credential Dumping Chain", 
            "OAuth Theft \u2192 Cloud Takeover Chain", "Cloud Takeover \u2192 Storage Exfiltration Chain"
        ]
    },
    "Logical Attack Scenarios": {
        "type": "sqli",
        "scenarios": [
            "Orphaned Account Abuse", "Stale Credential Abuse", "Excessive Permission Abuse", 
            "Misconfigured IAM Role Abuse", "Shared Account Abuse", "Weak Password Policy Abuse", 
            "Shadow IT Exploitation", "Forgotten Service Account Abuse", "Public Bucket Discovery", 
            "Exposed Secret Discovery"
        ]
    },
    "Enterprise Attacks": {
        "type": "phishing",
        "scenarios": [
            "Business Email Compromise", "Vendor Account Compromise", "Third-Party Access Abuse", 
            "Internal Ticketing System Abuse", "HR Portal Access Abuse", "Payroll Fraud Attempt", 
            "Executive Account Targeting", "Sensitive Document Access", "Internal Database Discovery", 
            "Customer Data Harvesting"
        ]
    },
    "Blackhat-Level Simulation": {
        "type": "exfiltration",
        "scenarios": [
            "Multi-Stage Intrusion Campaign", "Stealth Persistence Campaign", "Long-Term Data Collection", 
            "Advanced Credential Harvesting", "Multi-Hop Lateral Movement", "Cross-Domain Pivoting", 
            "Advanced Exfiltration Campaign", "Insider-Assisted Breach", "Hybrid Cloud Compromise", 
            "Enterprise-Wide Reconnaissance"
        ]
    },
    "Most Advanced Scenarios": {
        "type": "lateral_movement",
        "scenarios": [
            "Advanced Persistent Threat Simulation", "Nation-State Style Intrusion", 
            "Multi-Vector Attack Campaign", "Multi-Domain Takeover", "Cross-Forest Attack", 
            "Identity Infrastructure Compromise", "Enterprise Control Plane Compromise", 
            "Detection Evasion Campaign", "Multi-Stage Persistence Campaign", "Full Attack Lifecycle Simulation"
        ]
    },
    "Additional Scenarios": {
        "type": "ransomware",
        "scenarios": [
            "Ransomware Precursor Activity", "Ransomware Impact Simulation", "Backup Tampering Attempt", 
            "Recovery System Targeting", "Security Tool Evasion", "Endpoint Defense Bypass Attempt", 
            "SIEM Evasion Attempt", "SOAR Manipulation Attempt", "Threat Intelligence Poisoning", 
            "Enterprise Breach Simulation"
        ]
    }
}

# Semaphore to prevent overwhelming local socket and Postgres connection pools
SEMAPHORE = asyncio.Semaphore(15)

async def run_scenario_simulation(client: httpx.AsyncClient, category: str, sim_type: str, scenario_name: str) -> Dict[str, Any]:
    async with SEMAPHORE:
        payload = {
            "simulation_type": sim_type,
            "target": f"sys_node_{scenario_name.lower().replace(' ', '_')[:20]}",
            "parameters": {
                "scenario_name": scenario_name,
                "vector_description": f"BAS validation for {scenario_name}"
            }
        }
        
        start_time = time.time()
        try:
            # 1. Start simulation
            response = await client.post(f"{BASE_URL}/start_simulation", json=payload, timeout=10.0)
            if response.status_code != 200:
                return {
                    "category": category, "scenario": scenario_name, "type": sim_type, "simulation_id": None,
                    "status": "failed", "score": 0.0, "blocked": False, "error": f"HTTP status {response.status_code}"
                }
            
            sim_id = response.json().get("data", {}).get("simulation_id")
            if not sim_id:
                return {
                    "category": category, "scenario": scenario_name, "type": sim_type, "simulation_id": None,
                    "status": "failed", "score": 0.0, "blocked": False, "error": "No simulation_id in response"
                }
                
            # 2. Poll simulation results
            status = "running"
            score = 0.0
            max_retries = 35
            retry = 0
            
            while status == "running" and retry < max_retries:
                await asyncio.sleep(1.0)
                res_check = await client.get(f"{BASE_URL}/simulation_results/{sim_id}", timeout=5.0)
                
                if res_check.status_code == 200:
                    res_json = res_check.json()
                    status = res_json.get("data", {}).get("status", "running")
                    score = res_json.get("data", {}).get("score", 0.0)
                elif res_check.status_code == 404:
                    status = "running" # Keep waiting for async worker
                else:
                    status = "failed"
                    break
                retry += 1
                
            duration = time.time() - start_time
            blocked = (status == "prevented")
            
            return {
                "category": category,
                "scenario": scenario_name,
                "type": sim_type,
                "simulation_id": sim_id,
                "status": status,
                "score": score,
                "blocked": blocked,
                "error": None if status != "failed" else "Timeout or failed execution",
                "latency_ms": int(duration * 1000)
            }
            
        except Exception as e:
            return {
                "category": category,
                "scenario": scenario_name,
                "type": sim_type,
                "simulation_id": None,
                "status": "error",
                "score": 0.0,
                "blocked": False,
                "error": str(e)
            }

async def main():
    print("==========================================================")
    print("PHANTOMNET v4.0 — 130 ADVERSARY SCENARIOS ENTERPRISE RUN")
    print("==========================================================")
    print("[*] Ingesting all requested campaigns into BAS scheduler...")
    
    tasks = []
    async with httpx.AsyncClient() as client:
        for category, config in ATTACK_CATEGORIES.items():
            sim_type = config["type"]
            for scenario in config["scenarios"]:
                tasks.append(run_scenario_simulation(client, category, sim_type, scenario))
                
        print(f"[*] Queue initialized: {len(tasks)} distinct attack scenarios scheduled.")
        print("[*] Dispatching parallel worker pools (Semaphore Level: 15)...")
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
    print("\n==========================================================")
    print("ENTERPRISE VALIDATION RUN COMPLETED")
    print(f"Total Execution Time: {total_time:.2f} seconds")
    print(f"Average Pipeline Latency: {total_time/len(results):.3f} seconds/campaign")
    print("==========================================================")
    
    # Aggregation
    category_summary = {}
    total_blocked = 0
    total_detected = 0
    total_successful = 0
    total_failed = 0
    
    for r in results:
        cat = r["category"]
        if cat not in category_summary:
            category_summary[cat] = {"total": 0, "prevented": 0, "detected": 0, "successful": 0, "failed": 0}
            
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
        else:
            category_summary[cat]["failed"] += 1
            total_failed += 1
            
    # Print Dashboard
    print(f"\n{'THREAT CATEGORY':<40} | {'TOTAL':<5} | {'BLOCKED':<7} | {'DETECTED':<8} | {'SUCCESS':<7} | {'FAILED':<6}")
    print("-" * 88)
    for cat, counts in category_summary.items():
        print(f"{cat:<40} | {counts['total']:<5} | {counts['prevented']:<7} | {counts['detected']:<8} | {counts['successful']:<7} | {counts['failed']:<6}")
        
    print("-" * 88)
    print(f"{'TOTAL COMPREHENSIVE RUN':<40} | {len(results):<5} | {total_blocked:<7} | {total_detected:<8} | {total_successful:<7} | {total_failed:<6}")
    print("==========================================================")
    
    prevention_rate = (total_blocked / len(results)) * 100
    detection_rate = ((total_blocked + total_detected) / len(results)) * 100
    
    print(f"[*] Platform Ingestion Resilience Rate (Blocked): {prevention_rate:.1f}%")
    print(f"[*] Platform Overall Detection Rate (SIEM Maps): {detection_rate:.1f}%")
    print("==========================================================")
    
    # Save outcomes to JSON
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)
    print(f"[*] Bulk raw results successfully saved to {RESULTS_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
