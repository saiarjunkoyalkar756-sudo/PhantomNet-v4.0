# tests/scratch_attack_bench.py
import asyncio
import time
import json
import random
from backend_api.shared.bas_simulator import BASSimulator, AttackScenario

async def run_bulk_attack_simulation(attack_count: int = 120):
    print(f"🚀 Initializing PhantomNet XDR Threat Simulator...")
    print(f"⚡ Scheduling {attack_count} parallel breach attacks against enterprise assets...")
    
    simulator = BASSimulator()
    attack_types = ["phishing", "ransomware", "sqli"]
    assets = [
        "prod_database_cluster", "domain_controller", "finance_workstation_04",
        "file_server_prod", "hr_portal_web", "mail_exchange_gateway",
        "kubernetes_node_master", "vpn_gateway_ingress", "scada_hmi_controller"
    ]
    
    scenarios = []
    for i in range(attack_count):
        atk_type = random.choice(attack_types)
        scenario = AttackScenario(
            name=f"Threat-Campaign-{i+1:03d} ({atk_type.upper()})",
            description=f"Simulated mass breach campaign iteration {i+1}",
            attack_type=atk_type,
            target_asset=random.choice(assets),
            attack_vector="network" if atk_type == "ransomware" else ("email" if atk_type == "phishing" else "web_app"),
            risk_level=random.choice(["medium", "high", "critical"])
        )
        scenarios.append(scenario)
        
    start_time = time.time()
    
    # Run all 100+ simulations concurrently using asyncio.gather
    # We patch or override sleep internally or use gather to execute all at once
    # We mock or use small sleeps to speed up execution of 120 threats under 1.5 seconds
    tasks = []
    for scenario in scenarios:
        # Patch sleep to make benchmark extremely fast
        # To avoid blocking, we run simulated attacks with negligible sleeps
        # Since BASSimulator awaits asyncio.sleep, we run them all concurrently
        tasks.append(simulator.run_simulation(scenario))
        
    print(f"🔥 Executing attacks concurrently...")
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
    print("🏆 PHANTOMNET XDR BREACH SIMULATION REPORT")
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
    asyncio.run(run_bulk_attack_simulation(120))
