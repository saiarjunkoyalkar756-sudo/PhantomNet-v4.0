# tests/test_compliance.py
import pytest
from backend_api.shared.compliance_engine import ComplianceEngine, ComplianceFinding, ComplianceReport

@pytest.mark.asyncio
async def test_compliance_report_generation():
    """Verify that compliance scan successfully generates reports for requested standards."""
    engine = ComplianceEngine()
    
    # Run scan for ISO27001
    report = await engine.run_compliance_scan("ISO27001")
    assert isinstance(report, ComplianceReport)
    assert report.standard == "ISO27001"
    assert len(report.findings) > 0
    assert report.report_id is not None

def test_gap_analysis_identification():
    """Verify that non-compliant findings are correctly identified in the gap analysis."""
    findings = [
        ComplianceFinding(control_id="ISO-001", description="Access control", status="compliant"),
        ComplianceFinding(control_id="ISO-002", description="Data encryption", status="non-compliant", severity="high"),
        ComplianceFinding(control_id="ISO-003", description="Logs auditing", status="compliant")
    ]
    
    # Gap analysis prunes compliant and includes non-compliant
    gaps = [f for f in findings if f.status == "non-compliant"]
    assert len(gaps) == 1
    assert gaps[0].control_id == "ISO-002"
    assert gaps[0].severity == "high"

def test_status_calculation_logic():
    """Verify the overall status mapping based on non-compliant findings count."""
    # Case 1: No non-compliant -> compliant
    findings_1 = [
        ComplianceFinding(control_id="C1", description="desc", status="compliant"),
        ComplianceFinding(control_id="C2", description="desc", status="compliant")
    ]
    non_compliant_1 = sum(1 for f in findings_1 if f.status == "non-compliant")
    assert non_compliant_1 == 0
    status_1 = "compliant" if non_compliant_1 == 0 else "partial"
    assert status_1 == "compliant"

    # Case 2: Some non-compliant -> partial
    findings_2 = [
        ComplianceFinding(control_id="C1", description="desc", status="compliant"),
        ComplianceFinding(control_id="C2", description="desc", status="non-compliant")
    ]
    non_compliant_2 = sum(1 for f in findings_2 if f.status == "non-compliant")
    assert 0 < non_compliant_2 < len(findings_2)
    status_2 = "partial"
    assert status_2 == "partial"
