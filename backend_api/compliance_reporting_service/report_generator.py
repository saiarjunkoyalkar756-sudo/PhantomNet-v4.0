# backend_api/compliance_reporting_service/report_generator.py
import os
from fpdf import FPDF
from datetime import datetime
from typing import Dict, Any, List

class CompliancePDFGenerator(FPDF):
    def header(self):
        # Logo placeholder
        self.set_font("helvetica", "B", 15)
        self.cell(80)
        self.cell(30, 10, "PhantomNet Compliance Report", border=0, align="C")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def generate_report(self, report_data: Dict[str, Any], output_path: str):
        self.add_page()
        self.set_font("helvetica", "", 12)
        
        # Summary Section
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, f"Report Type: {report_data.get('standard', 'N/A').upper()}", ln=True)
        self.set_font("helvetica", "", 12)
        self.cell(0, 10, f"Report ID: {report_data.get('report_id')}", ln=True)
        self.cell(0, 10, f"Generated At: {report_data.get('generated_at')}", ln=True)
        self.cell(0, 10, f"Overall Score: {report_data.get('details', {}).get('compliance_score', 0)}%", ln=True)
        self.ln(10)

        # Findings Table
        self.set_font("helvetica", "B", 12)
        self.cell(40, 10, "Control ID", border=1)
        self.cell(40, 10, "Status", border=1)
        self.cell(110, 10, "Description", border=1)
        self.ln()

        self.set_font("helvetica", "", 10)
        for finding in report_data.get("details", {}).get("findings", []):
            self.cell(40, 10, str(finding.get("control_id")), border=1)
            
            # Color coding for status
            status = finding.get("status", "Unknown")
            if status == "Compliant":
                self.set_text_color(0, 128, 0)
            else:
                self.set_text_color(255, 0, 0)
                
            self.cell(40, 10, status, border=1)
            self.set_text_color(0, 0, 0)
            self.cell(110, 10, str(finding.get("description")[:50]), border=1)
            self.ln()

        # Save to file
        self.output(output_path)
        return output_path

def generate_pdf_report(report_data: Dict[str, Any], output_dir: str = "reports") -> str:
    """
    Entry point for generating a compliance PDF.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"Report_{report_data.get('report_id')}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    pdf = CompliancePDFGenerator()
    pdf.generate_report(report_data, filepath)
    
    return filepath
