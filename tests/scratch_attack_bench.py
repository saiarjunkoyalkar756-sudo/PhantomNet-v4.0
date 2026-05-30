# tests/scratch_attack_bench.py
import asyncio
import time
import json
import random
from backend_api.shared.bas_simulator import BASSimulator, AttackScenario

async def run_bulk_attack_simulation(attack_count: int = 150):
    print(f"🚀 Initializing PhantomNet XDR Threat Simulator (v4.0 Advanced)...")
    print(f"⚡ Scheduling {attack_count} parallel breach attacks against enterprise assets...")
    
    simulator = BASSimulator()
    attack_types = [
        "phishing", "ransomware", "sqli", 
        "lateral_movement", "credential_access", "privilege_escalation", "exfiltration"
    ]
    assets = [
        "prod_database_cluster", "domain_controller", "finance_workstation_04",
        "file_server_prod", "hr_portal_web", "mail_exchange_gateway",
        "kubernetes_node_master", "vpn_gateway_ingress", "scada_hmi_controller"
    ]
    
    scenarios = []
    for i in range(attack_count):
        atk_type = random.choice(attack_types)
        
        # Select realistic attack vectors per type
        if atk_type == "phishing":
            vector = "email"
        elif atk_type == "sqli":
            vector = "web_app"
        elif atk_type in ["ransomware", "lateral_movement"]:
            vector = "network"
        elif atk_type in ["credential_access", "privilege_escalation"]:
            vector = "host_agent"
        else:  # exfiltration
            vector = "network_egress"
            
        scenario = AttackScenario(
            name=f"Threat-Campaign-{i+1:03d} ({atk_type.upper()})",
            description=f"Simulated mass breach campaign iteration {i+1} utilizing {atk_type}",
            attack_type=atk_type,
            target_asset=random.choice(assets),
            attack_vector=vector,
            risk_level=random.choice(["medium", "high", "critical"])
        )
        scenarios.append(scenario)
        
    start_time = time.time()
    
    # Run all simulations concurrently using asyncio.gather
    tasks = []
    for scenario in scenarios:
        tasks.append(simulator.run_simulation(scenario))
        
    print(f"🔥 Executing advanced attacks concurrently...")
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    # Process Metrics
    total_duration = end_time - start_time
    detected_count = 0
    prevented_count = 0
    successful_count = 0
    total_score = 0.0
    
    for r in results:
        total_score += r.score
        if r.status == "detected":
            detected_count += 1
        elif r.status == "prevented":
            prevented_count += 1
        elif r.status == "successful":
            successful_count += 1
            
    avg_score = total_score / attack_count
    
    print("\n" + "="*60)
    print("🏆 PHANTOMNET XDR BREACH SIMULATION REPORT (ADVANCED CAMPAIGN)")
    print("="*60)
    print(f"🔹 Total Attacks Simulated  : {attack_count}")
    print(f"🔹 Concurrent Time Elapsed  : {total_duration:.2f} seconds")
    print(f"🔹 Avg Defensive Score      : {avg_score:.2f} / 100")
    print("-"*60)
    print(f"✅ Attacks Blocked/Prevented: {prevented_count} ({(prevented_count/attack_count)*100:.1f}%)")
    print(f"🔍 Attacks Detected by XDR : {detected_count} ({(detected_count/attack_count)*100:.1f}%)")
    print(f"⚠️  Attacks Successful (Slipped): {successful_count} ({(successful_count/attack_count)*100:.1f}%)")
    print("="*60)
    
if __name__ == "__main__":
    asyncio.run(run_bulk_attack_simulation(150))
