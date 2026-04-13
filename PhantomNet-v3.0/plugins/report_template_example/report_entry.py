# plugins/report_template_example/report_entry.py
import json
import datetime

def generate_report(report_data: dict, output_format: str = "text") -> dict:
    """
    Simulates generating a security report from provided data.
    """
    print(f"[{__name__}] Generating report in {output_format} format...")

    report_title = report_data.get("title", "Security Summary Report")
    report_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    findings = report_data.get("findings", [])
    summary = report_data.get("summary", "No summary provided.")

    report_content = ""
    if output_format == "text":
        report_content += f"--- {report_title} ---\n"
        report_content += f"Date: {report_date}\n\n"
        report_content += f"Summary:\n{summary}\n\n"
        report_content += "Findings:\n"
        if findings:
            for i, finding in enumerate(findings):
                report_content += f"  {i+1}. {finding.get('description', 'N/A')} (Severity: {finding.get('severity', 'Low')})\n"
        else:
            report_content += "  No significant findings.\n"
        report_content += "\n--- End of Report ---\n"
    elif output_format == "json":
        report_content = json.dumps({
            "title": report_title,
            "date": report_date,
            "summary": summary,
            "findings": findings
        }, indent=2)
    else:
        return {"error": f"Unsupported output format: {output_format}"}

    # In a real scenario, this would write to a file or a database
    # For now, we return the content directly
    return {"status": "success", "report_content": report_content, "format": output_format}

if __name__ == "__main__":
    # Example usage for local testing
    test_report_data = {
        "title": "Weekly Vulnerability Scan Results",
        "summary": "Overall system health is good, but a few critical vulnerabilities were identified on external-facing services.",
        "findings": [
            {"description": "SQL Injection vulnerability on /api/users", "severity": "Critical"},
            {"description": "Outdated library in dashboard_frontend", "severity": "High"},
            {"description": "Weak password policy detected", "severity": "Medium"}
        ]
    }

    print(f"--- Testing Basic Security Report Plugin (Text Format) ---")
    text_report_output = generate_report(test_report_data, output_format="text")
    print(text_report_output["report_content"])
    print("-------------------------------------------------------")

    print(f"\n--- Testing Basic Security Report Plugin (JSON Format) ---")
    json_report_output = generate_report(test_report_data, output_format="json")
    print(json_report_output["report_content"])
    print("--------------------------------------------------------")
