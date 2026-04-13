# backend_api/mitre_attack_integration.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import random
import uuid

# --- Data Models for MITRE ATT&CK ---
class Technique(BaseModel):
    id: str = Field(..., description="MITRE ATT&CK Technique ID (e.g., T1003)")
    name: str = Field(..., description="Technique Name (e.g., OS Credential Dumping)")
    description: Optional[str] = Field(None, description="Short description of the technique")
    tactics: List[str] = Field([], description="List of tactics associated with this technique")

class Tactic(BaseModel):
    id: str = Field(..., description="MITRE ATT&CK Tactic ID")
    name: str = Field(..., description="Tactic Name (e.g., Credential Access)")
    description: Optional[str] = Field(None, description="Short description of the tactic")

class AttackMappingResult(BaseModel):
    finding_id: str = Field(..., description="ID of the security finding")
    mapped_techniques: List[Technique] = Field([], description="List of mapped ATT&CK techniques")
    confidence: float = Field(..., ge=0, le=1.0, description="Confidence of the mapping")
    explanation: Optional[str] = Field(None, description="Explanation for the mapping")

class AttackCoverageScore(BaseModel):
    tactic: Tactic = Field(..., description="ATT&CK Tactic being scored")
    techniques_covered: int = Field(..., ge=0, description="Number of techniques covered under this tactic")
    total_techniques_in_tactic: int = Field(..., ge=0, description="Total techniques under this tactic")
    coverage_percentage: float = Field(..., ge=0, le=100.0, description="Percentage of techniques covered")
    ai_score_explanation: Optional[str] = Field(None, description="AI's explanation for the coverage score")

# --- Simulated ATT&CK Data ---
# In a real system, this would be loaded from a comprehensive source like Mitre CTI
SIMULATED_TACTICS: Dict[str, Tactic] = {
    "TA0001": Tactic(id="TA0001", name="Initial Access", description="Gaining initial footholds within a network."),
    "TA0002": Tactic(id="TA0002", name="Execution", description="Running malicious code."),
    "TA0003": Tactic(id="TA0003", name="Persistence", description="Maintaining access."),
    "TA0004": Tactic(id="TA0004", name="Privilege Escalation", description="Gaining higher-level permissions."),
    "TA0006": Tactic(id="TA0006", name="Credential Access", description="Stealing credentials."),
    "TA0008": Tactic(id="TA0008", name="Lateral Movement", description="Moving through the environment."),
}

SIMULATED_TECHNIQUES: List[Technique] = [
    Technique(id="T1190", name="Exploit Public-Facing Application", tactics=["TA0001"], description="Exploitation of vulnerabilities in internet-facing apps."),
    Technique(id="T1078", name="Valid Accounts", tactics=["TA0001", "TA0003", "TA0006"], description="Use of legitimate credentials."),
    Technique(id="T1059.003", name="Command and Scripting Interpreter: Windows Command Shell", tactics=["TA0002"], description="Use of cmd.exe."),
    Technique(id="T1003", name="OS Credential Dumping", tactics=["TA0006"], description="Harvesting credentials from the operating system."),
    Technique(id="T1021.001", name="Remote Services: Remote Desktop Protocol", tactics=["TA0008"], description="Use of RDP for lateral movement."),
    Technique(id="T1098", name="Account Manipulation", tactics=["TA0003"], description="Adversary modifies account properties to maintain access."),
    Technique(id="T1087", name="Account Discovery", tactics=["TA0007"], description="Adversary attempts to get a listing of accounts on a system or domain.")
]

def get_all_techniques() -> List[Technique]:
    """Returns all simulated ATT&CK techniques."""
    return SIMULATED_TECHNIQUES

def get_all_tactics() -> List[Tactic]:
    """Returns all simulated ATT&CK tactics."""
    return list(SIMULATED_TACTICS.values())

def map_finding_to_attack_techniques(finding_description: str) -> List[AttackMappingResult]:
    """
    Simulates mapping a security finding to relevant MITRE ATT&CK techniques.
    """
    mapped_results: List[AttackMappingResult] = []
    
    # Simple keyword-based mapping for simulation
    finding_lower = finding_description.lower()

    if "exploit" in finding_lower or "vulnerability" in finding_lower:
        mapped_results.append(AttackMappingResult(
            finding_id=str(uuid.uuid4()),
            mapped_techniques=[t for t in SIMULATED_TECHNIQUES if t.id == "T1190"],
            confidence=random.uniform(0.7, 0.9),
            explanation="Keyword 'exploit' or 'vulnerability' suggests public-facing application exploitation."
        ))
    if "credential" in finding_lower or "password" in finding_lower or "hash" in finding_lower:
        mapped_results.append(AttackMappingResult(
            finding_id=str(uuid.uuid4()),
            mapped_techniques=[t for t in SIMULATED_TECHNIQUES if t.id == "T1003"],
            confidence=random.uniform(0.8, 0.95),
            explanation="Keywords 'credential' or 'password' indicate credential access techniques."
        ))
    if "login failed" in finding_lower or "brute force" in finding_lower:
        mapped_results.append(AttackMappingResult(
            finding_id=str(uuid.uuid4()),
            mapped_techniques=[t for t in SIMULATED_TECHNIQUES if t.id == "T1078"],
            confidence=random.uniform(0.6, 0.85),
            explanation="Keywords 'login failed' or 'brute force' suggest valid accounts technique."
        ))
    if "remote desktop" in finding_lower or "rdp" in finding_lower:
        mapped_results.append(AttackMappingResult(
            finding_id=str(uuid.uuid4()),
            mapped_techniques=[t for t in SIMULATED_TECHNIQUES if t.id == "T1021.001"],
            confidence=random.uniform(0.75, 0.92),
            explanation="Keywords 'remote desktop' or 'RDP' suggest Remote Services: RDP for lateral movement."
        ))
    
    # If no specific mapping, suggest a generic one
    if not mapped_results:
        mapped_results.append(AttackMappingResult(
            finding_id=str(uuid.uuid4()),
            mapped_techniques=[t for t in SIMULATED_TECHNIQUES if t.id == random.choice(["T1078", "T1190"])], # Random fallback
            confidence=random.uniform(0.3, 0.6),
            explanation="No direct keyword match, inferred general access technique."
        ))

    return mapped_results

def get_ai_attack_coverage_scoring(findings: List[str]) -> List[AttackCoverageScore]:
    """
    Simulates AI-based ATT&CK matrix coverage scoring.
    Takes a list of finding descriptions and calculates coverage based on mapped techniques.
    """
    all_mapped_techniques_ids = set()
    for finding_desc in findings:
        mappings = map_finding_to_attack_techniques(finding_desc)
        for mapping in mappings:
            for tech in mapping.mapped_techniques:
                all_mapped_techniques_ids.add(tech.id)
    
    coverage_scores: List[AttackCoverageScore] = []
    for tactic_id, tactic_obj in SIMULATED_TACTICS.items():
        techniques_in_tactic = [t for t in SIMULATED_TECHNIQUES if tactic_obj.name in t.tactics]
        total_techniques_in_tactic = len(techniques_in_tactic)
        
        covered_techniques_count = 0
        for tech in techniques_in_tactic:
            if tech.id in all_mapped_techniques_ids:
                covered_techniques_count += 1
        
        coverage_percentage = (covered_techniques_count / total_techniques_in_tactic * 100) if total_techniques_in_tactic > 0 else 0
        
        ai_explanation = f"AI estimates {covered_techniques_count} out of {total_techniques_in_tactic} techniques under '{tactic_obj.name}' tactic are addressed or detected. Focus on improving coverage for unaddressed techniques."

        coverage_scores.append(AttackCoverageScore(
            tactic=tactic_obj,
            techniques_covered=covered_techniques_count,
            total_techniques_in_tactic=total_techniques_in_tactic,
            coverage_percentage=round(coverage_percentage, 2),
            ai_score_explanation=ai_explanation
        ))
    
    return coverage_scores


if __name__ == "__main__":
    print("--- Testing MITRE ATT&CK Integration ---")

    # Test mapping
    finding1 = "Discovered SQL Injection vulnerability on /admin portal. Credentials exposed."
    mapping_results = map_finding_to_attack_techniques(finding1)
    print("\nMapping Results for:", finding1)
    for res in mapping_results:
        print(f"  Confidence: {res.confidence}, Explanation: {res.explanation}")
        for tech in res.mapped_techniques:
            print(f"    - Technique: {tech.name} ({tech.id})")

    finding2 = "Failed brute-force login attempts detected on SSH."
    mapping_results2 = map_finding_to_attack_techniques(finding2)
    print("\nMapping Results for:", finding2)
    for res in mapping_results2:
        print(f"  Confidence: {res.confidence}, Explanation: {res.explanation}")
        for tech in res.mapped_techniques:
            print(f"    - Technique: {tech.name} ({tech.id})")

    # Test coverage scoring
    sample_findings = [
        "Identified CVE-2023-1234 on web server, potentially leading to initial access.",
        "Detected unauthorized RDP login from external IP, followed by credential dumping.",
        "Multiple failed login attempts against domain controllers."
    ]
    coverage_scores = get_ai_attack_coverage_scoring(sample_findings)
    print("\n--- AI ATT&CK Coverage Scoring ---")
    for score in coverage_scores:
        print(f"Tactic: {score.tactic.name} ({score.tactic.id})")
        print(f"  Coverage: {score.coverage_percentage:.2f}% ({score.techniques_covered}/{score.total_techniques_in_tactic})")
        print(f"  AI Explanation: {score.ai_score_explanation}")
        print("-" * 20)
