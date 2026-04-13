# backend_api/compliance_engine.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import random
import time
import uuid


# --- Data Models for Compliance Reporting ---
class ComplianceFinding(BaseModel):
    control_id: str = Field(..., description="ID of the compliance control")
    description: str = Field(..., description="Description of the finding")
    status: str = Field(
        ..., description="Compliance status ('compliant', 'non-compliant', 'n/a')"
    )
    evidence: Optional[str] = Field(None, description="Evidence supporting the status")
    severity: str = Field(
        "medium",
        description="Severity of non-compliance ('low', 'medium', 'high', 'critical')",
    )


class ComplianceHeatmap(BaseModel):
    control_area: str = Field(
        ...,
        description="High-level control area (e.g., 'Access Control', 'Data Protection')",
    )
    compliant_percentage: float = Field(
        ..., ge=0, le=100, description="Percentage of compliant controls in this area"
    )
    non_compliant_count: int = Field(
        ..., ge=0, description="Number of non-compliant controls"
    )
    total_controls: int = Field(..., ge=0, description="Total controls in this area")


class ImprovementPlanRecommendation(BaseModel):
    recommendation_id: str = Field(..., description="Unique ID for the recommendation")
    control_id: str = Field(..., description="Related compliance control ID")
    description: str = Field(
        ..., description="Detailed description of the recommendation"
    )
    priority: str = Field(..., description="Priority ('low', 'medium', 'high')")
    estimated_effort: str = Field(
        ..., description="Estimated effort ('low', 'medium', 'high')"
    )
    ai_rationale: Optional[str] = Field(
        None, description="AI-generated rationale for the recommendation"
    )


class ComplianceReport(BaseModel):
    report_id: str = Field(..., description="Unique ID for the report")
    standard: str = Field(
        ..., description="Compliance standard (e.g., 'ISO27001', 'SOC2')"
    )
    timestamp: float = Field(
        default_factory=time.time, description="Timestamp of report generation"
    )
    overall_status: str = Field(
        ...,
        description="Overall compliance status ('compliant', 'non-compliant', 'partial')",
    )
    findings: List[ComplianceFinding] = Field(
        [], description="List of individual compliance findings"
    )
    heatmap: List[ComplianceHeatmap] = Field([], description="Summary heatmap data")
    gap_analysis: List[ComplianceFinding] = Field(
        [], description="List of non-compliant findings (gaps)"
    )
    ai_improvement_plan: List[ImprovementPlanRecommendation] = Field(
        [], description="AI-generated improvement plan"
    )


class ComplianceEngine:
    def __init__(self):
        self.reports: Dict[str, ComplianceReport] = {}  # Store generated reports

    async def _simulate_compliance_check(
        self, standard: str
    ) -> List[ComplianceFinding]:
        """Simulates checking compliance against a standard."""
        time.sleep(random.uniform(2, 5))  # Simulate work
        findings = []
        num_findings = random.randint(5, 15)
        for i in range(num_findings):
            status_choice = random.choice(["compliant", "non-compliant", "n/a"])
            severity_choice = "medium"
            if status_choice == "non-compliant":
                severity_choice = random.choice(["low", "medium", "high", "critical"])

            findings.append(
                ComplianceFinding(
                    control_id=f"{standard}-C{i+1:03d}",
                    description=f"Control {i+1} for {standard}",
                    status=status_choice,
                    evidence=(
                        f"Log files, configuration, policy doc {random.randint(100,999)}"
                        if status_choice == "compliant"
                        else None
                    ),
                    severity=severity_choice,
                )
            )
        return findings

    async def _generate_heatmap(
        self, findings: List[ComplianceFinding]
    ) -> List[ComplianceHeatmap]:
        """Simulates generating a compliance heatmap."""
        time.sleep(random.uniform(0.5, 1.5))
        control_areas = [
            "Access Control",
            "Data Protection",
            "Incident Response",
            "Risk Management",
            "Security Operations",
        ]
        heatmap_data = []
        for area in control_areas:
            total = random.randint(5, 20)
            non_compliant = random.randint(0, total // 3)
            compliant_pct = (
                ((total - non_compliant) / total * 100) if total > 0 else 100
            )
            heatmap_data.append(
                ComplianceHeatmap(
                    control_area=area,
                    compliant_percentage=round(compliant_pct, 2),
                    non_compliant_count=non_compliant,
                    total_controls=total,
                )
            )
        return heatmap_data

    async def _generate_improvement_plan(
        self, gap_analysis: List[ComplianceFinding]
    ) -> List[ImprovementPlanRecommendation]:
        """Simulates AI-generated improvement plan."""
        time.sleep(random.uniform(1, 3))
        recommendations = []
        for finding in gap_analysis:
            if finding.status == "non-compliant":
                priority = random.choice(["low", "medium", "high"])
                effort = random.choice(["low", "medium", "high"])
                recommendations.append(
                    ImprovementPlanRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        control_id=finding.control_id,
                        description=f"Implement compensating control for {finding.control_id} due to '{finding.description}'. Review existing policies.",
                        priority=priority,
                        estimated_effort=effort,
                        ai_rationale=(
                            "Identified as a critical vulnerability affecting data integrity and confidentiality. Prompt remediation is recommended."
                            if priority == "high"
                            else None
                        ),
                    )
                )
        return recommendations

    async def run_compliance_scan(self, standard: str) -> ComplianceReport:
        """
        Runs a simulated compliance scan for a given standard and generates a report.
        """
        report_id = str(uuid.uuid4())
        logger.info(
            f"[{__name__}] Starting compliance scan for {standard} (Report ID: {report_id})"
        )

        # Simulate compliance checks
        findings = await self._simulate_compliance_check(standard)

        # Determine overall status
        non_compliant_count = sum(1 for f in findings if f.status == "non-compliant")
        if non_compliant_count == 0:
            overall_status = "compliant"
        elif non_compliant_count == len(findings):
            overall_status = "non-compliant"
        else:
            overall_status = "partial"

        # Generate heatmap
        heatmap = await self._generate_heatmap(findings)

        # Perform gap analysis
        gap_analysis = [f for f in findings if f.status == "non-compliant"]

        # Generate AI improvement plan
        ai_improvement_plan = await self._generate_improvement_plan(gap_analysis)

        report = ComplianceReport(
            report_id=report_id,
            standard=standard,
            overall_status=overall_status,
            findings=findings,
            heatmap=heatmap,
            gap_analysis=gap_analysis,
            ai_improvement_plan=ai_improvement_plan,
        )
        self.reports[report_id] = report
        logger.info(
            f"[{__name__}] Completed compliance scan for {standard}. Report ID: {report_id}, Status: {overall_status}"
        )
        return report

    def get_compliance_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Retrieves a previously generated compliance report."""
        return self.reports.get(report_id)

    def get_all_reports(self) -> List[ComplianceReport]:
        """Retrieves all generated compliance reports."""
        return list(self.reports.values())


if __name__ == "__main__":
    engine = ComplianceEngine()

    async def test_compliance_engine():
        print("--- Testing ISO27001 Compliance Scan ---")
        iso_report = await engine.run_compliance_scan("ISO27001")
        print(json.dumps(iso_report.dict(), indent=2))

        print("\n--- Testing SOC2 Compliance Scan ---")
        soc2_report = await engine.run_compliance_scan("SOC2")
        print(json.dumps(soc2_report.dict(), indent=2))

        print(f"\n--- Retrieving Report {iso_report.report_id} ---")
        retrieved_iso = engine.get_compliance_report(iso_report.report_id)
        (
            print(json.dumps(retrieved_iso.dict(), indent=2))
            if retrieved_iso
            else "Report not found."
        )

        print("\n--- Retrieving All Reports ---")
        all_reports = engine.get_all_reports()
        print(json.dumps([r.dict() for r in all_reports], indent=2))

    asyncio.run(test_compliance_engine())
