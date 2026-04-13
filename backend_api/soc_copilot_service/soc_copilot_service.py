# backend_api/soc_copilot_service/soc_copilot_service.py

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from typing import Dict, Any, List, Optional
import httpx # For calling LLM APIs

from shared.logger_config import logger
from .schemas import AlertExplanationRequest, AlertExplanationResponse, InvestigationRequest, InvestigationResponse, RuleGenerationRequest, GeneratedRule, ThreatReportRequest, ThreatReportResponse, InvestigationStep

# Import conceptual context builder
from .context_builder_service import ContextBuilder

logger = logger

# --- Configuration for LLM ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com/v1"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GOOGLE_GEMINI_API_KEY")
# ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")

DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gpt-3.5-turbo")
# Alternatively for Google Gemini: "gemini-pro"

class SOCCopilotService:
    """
    Implements the PhantomNet SOC AI Copilot functionalities,
    interacting with LLMs and other backend services.
    """
    def __init__(self):
        self.httpx_client = httpx.AsyncClient()
        self.context_builder = ContextBuilder()
        logger.info(f"SOCCopilotService initialized. Default LLM: {DEFAULT_LLM_MODEL}")

        if OPENAI_API_KEY == "YOUR_OPENAI_API_KEY" and GEMINI_API_KEY == "YOUR_GOOGLE_GEMINI_API_KEY":
            logger.warning("No LLM API keys configured. Copilot will use canned/mocked responses.")
            self._mock_llm_mode = True
        else:
            self._mock_llm_mode = False

    async def _call_llm(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """
        Generic function to call an LLM (OpenAI or Gemini).
        """
        if self._mock_llm_mode:
            logger.info("LLM in mock mode. Returning canned response.")
            return "This is a mock LLM response based on your request."

        if DEFAULT_LLM_MODEL.startswith("gpt"):
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": DEFAULT_LLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            try:
                response = await self.httpx_client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenAI API HTTP error: {e.response.status_code} - {e.response.text}")
                return f"Error calling OpenAI API: {e.response.text}"
            except Exception as e:
                logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
                return f"Error calling OpenAI API: {e}"
        
        elif DEFAULT_LLM_MODEL.startswith("gemini"):
            # Google Gemini API integration (conceptual - specific client library often used)
            # This is a simplified direct HTTP call for demonstration
            if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GOOGLE_GEMINI_API_KEY":
                logger.warning("Gemini API key not configured. Cannot call Gemini.")
                return "Gemini API key not configured."
            
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            try:
                # Placeholder for Gemini API endpoint structure
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_LLM_MODEL}:generateContent?key={GEMINI_API_KEY}"
                response = await self.httpx_client.post(gemini_url, headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except httpx.HTTPStatusError as e:
                logger.error(f"Gemini API HTTP error: {e.response.status_code} - {e.response.text}")
                return f"Error calling Gemini API: {e.response.text}"
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}", exc_info=True)
                return f"Error calling Gemini API: {e}"

        logger.warning(f"Unsupported LLM model: {DEFAULT_LLM_MODEL}")
        return "Unsupported LLM model configuration."

    async def explain_alert(self, request: AlertExplanationRequest) -> AlertExplanationResponse:
        """
        Uses LLM to explain an alert, its potential impact, and recommended actions.
        """
        logger.info(f"Explaining alert: {request.alert_title}")
        prompt = f"""
        Explain the following cybersecurity alert in simple terms for a SOC analyst.
        Provide potential impact and recommended immediate actions.
        
        Alert Title: {request.alert_title}
        Alert Description: {request.alert_description}
        Alert Context: {json.dumps(request.alert_context, indent=2)}
        """
        llm_response_text = await self._call_llm(prompt)
        
        # Parse LLM response (conceptual - might need more robust parsing)
        explanation = "No explanation generated."
        potential_impact = []
        recommended_actions = []

        if "Explanation:" in llm_response_text:
            parts = llm_response_text.split("Explanation:")
            explanation = parts[1].split("Potential Impact:")[0].strip() if "Potential Impact:" in parts[1] else parts[1].strip()
            
            if "Potential Impact:" in llm_response_text:
                impact_part = llm_response_text.split("Potential Impact:")[1].split("Recommended Actions:")[0].strip()
                potential_impact = [line.strip() for line in impact_part.split('\n') if line.strip()]
            
            if "Recommended Actions:" in llm_response_text:
                actions_part = llm_response_text.split("Recommended Actions:")[1].strip()
                recommended_actions = [line.strip() for line in actions_part.split('\n') if line.strip()]

        return AlertExplanationResponse(
            explanation=explanation,
            potential_impact=potential_impact,
            recommended_actions=recommended_actions,
            confidence=0.8 # Conceptual confidence
        )

    async def auto_investigate(self, request: InvestigationRequest) -> InvestigationResponse:
        """
        Uses LLM and other services (TI, SIEM) to perform simulated investigation steps.
        """
        logger.info(f"Auto-investigating indicator: {request.indicator_value} ({request.indicator_type})")
        investigation_steps = []
        
        # Step 1: Enrich indicator via Threat Intelligence Service
        # from backend_api.threat_intelligence_service.enrichment import ThreatIntelligenceEnricher
        # ti_enricher = ThreatIntelligenceEnricher()
        # ti_result = await ti_enricher.enrich_indicator(request.indicator_value, request.indicator_type)
        
        # Mock TI enrichment
        ti_result_mock = {"reputation_score": 75, "threat_tags": ["malicious", "botnet"], "source": "VirusTotal"}
        investigation_steps.append(InvestigationStep(
            step_description=f"Enriching {request.indicator_type} {request.indicator_value} using Threat Intelligence.",
            tool_used="ThreatIntelService",
            output={"ti_result": ti_result_mock}
        ))
        
        # Step 2: Query SIEM for historical logs related to indicator
        # from backend_api.siem_integration_service.phantomql_engine import PhantomQLEngine
        # siem_engine = PhantomQLEngine()
        # siem_query = PhantomQLQuery(query_string=f"source_ip='{request.indicator_value}' OR destination_ip='{request.indicator_value}'")
        # siem_results = await siem_engine.query_logs(siem_query)
        
        # Mock SIEM query
        siem_results_mock = {"total_hits": 5, "logs_sample": ["log1", "log2"]}
        investigation_steps.append(InvestigationStep(
            step_description=f"Querying SIEM for logs related to {request.indicator_value}.",
            tool_used="SIEMService",
            output={"siem_results": siem_results_mock}
        ))

        # Use LLM to summarize findings and suggest next steps
        prompt = f"""
        Based on the following investigation steps, summarize the findings for indicator {request.indicator_value} ({request.indicator_type}).
        Provide a conclusion and recommended remediation actions.
        
        Investigation Steps: {json.dumps([s.model_dump() for s in investigation_steps], indent=2)}
        Initial Alert ID: {request.initial_alert_id}
        """
        llm_response_text = await self._call_llm(prompt, max_tokens=1000)

        summary = "No summary generated."
        conclusion = "No conclusion."
        recommended_remediation = []

        # Simple parsing for demonstration
        if "Summary:" in llm_response_text:
            parts = llm_response_text.split("Summary:")
            summary = parts[1].split("Conclusion:")[0].strip() if "Conclusion:" in parts[1] else parts[1].strip()
            
            if "Conclusion:" in llm_response_text:
                conclusion_part = llm_response_text.split("Conclusion:")[1].split("Recommended Remediation:")[0].strip()
                conclusion = conclusion_part.strip()
            
            if "Recommended Remediation:" in llm_response_text:
                remediation_part = llm_response_text.split("Recommended Remediation:")[1].strip()
                recommended_remediation = [line.strip() for line in remediation_part.split('\n') if line.strip()]

        return InvestigationResponse(
            summary=summary,
            conclusion=conclusion,
            steps_taken=investigation_steps,
            identified_threats=[ti_result_mock], # Add TI results as identified threats
            recommended_remediation=recommended_remediation
        )

    async def write_detection_rule(self, request: RuleGenerationRequest) -> GeneratedRule:
        """
        Generates YARA/Sigma rule snippets based on an event pattern using LLM.
        """
        logger.info(f"Generating {request.rule_type} rule for pattern: {request.event_pattern}")
        prompt = f"""
        Generate a {request.rule_type} rule based on the following event pattern and context.
        Provide a rule name, description, and map to relevant MITRE ATT&CK techniques if possible.
        
        Event Pattern: {json.dumps(request.event_pattern, indent=2)}
        Context: {request.context_info or "None"}
        """
        llm_response_text = await self._call_llm(prompt, max_tokens=700)
        
        rule_name = "generated_rule"
        rule_description = "AI-generated rule."
        rule_content = llm_response_text
        mitre_techniques = []

        # Example parsing
        if "Rule Name:" in llm_response_text:
            rule_name = llm_response_text.split("Rule Name:")[1].split("\n")[0].strip()
        if "Description:" in llm_response_text:
            rule_description = llm_response_text.split("Description:")[1].split("Rule Content:")[0].strip()
        if "Rule Content:" in llm_response_text:
            rule_content = llm_response_text.split("Rule Content:")[1].split("MITRE Techniques:")[0].strip()
        if "MITRE Techniques:" in llm_response_text:
            mitre_techniques = [t.strip() for t in llm_response_text.split("MITRE Techniques:")[1].split('\n') if t.strip()]

        return GeneratedRule(
            rule_type=request.rule_type,
            rule_content=rule_content,
            rule_name=rule_name,
            description=rule_description,
            mitre_techniques=mitre_techniques,
            confidence=0.7 # Conceptual
        )

    async def generate_threat_report(self, request: ThreatReportRequest) -> ThreatReportResponse:
        """
        Compiles data for a threat report based on an incident using LLM.
        """
        logger.info(f"Generating {request.report_type} threat report for incident: {request.incident_id}")
        
        # Conceptual gathering of incident data (e.g., from Case Management, SIEM, SOAR)
        incident_data_mock = {
            "incident_id": request.incident_id,
            "title": "Simulated Phishing Campaign",
            "involved_indicators": ["bad.domain.com", "1.1.1.1"],
            "remediation_actions": ["IP blocked", "User warned"],
            "alerts": ["Alert-1", "Alert-2"]
        }

        prompt = f"""
        Generate a {request.report_type} threat report for the following incident.
        Include a summary, key findings, and recommended long-term actions.
        
        Incident Data: {json.dumps(incident_data_mock, indent=2)}
        Additional Context: {request.additional_context or "None"}
        """
        llm_response_text = await self._call_llm(prompt, max_tokens=1500)

        report_title = f"Threat Report for Incident {request.incident_id}"
        report_summary = "No summary generated."
        report_content = llm_response_text

        return ThreatReportResponse(
            report_title=report_title,
            report_summary=report_summary,
            report_content=report_content,
            related_indicators=incident_data_mock["involved_indicators"]
        )

# Example usage (for testing purposes)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running SOCCopilotService example...")
    
    # Needs uuid import
    import uuid
    from unittest.mock import patch, AsyncMock

    async def run_example():
        copilot = SOCCopilotService()
        
        # Mock LLM calls if in mock mode
        if copilot._mock_llm_mode:
            with patch.object(copilot, '_call_llm', AsyncMock(return_value="Mock LLM response for testing.")) as mock_llm:
                # Test explain_alert
                alert_req = AlertExplanationRequest(
                    alert_title="Malicious IP Activity",
                    alert_description="Multiple failed login attempts from a blacklisted IP.",
                    alert_context={"source_ip": "1.1.1.1", "user_id": "johndoe"}
                )
                explanation_res = await copilot.explain_alert(alert_req)
                logger.info(f"\nAlert Explanation:\n{explanation_res.model_dump_json(indent=2)}")

                # Test auto_investigate
                invest_req = InvestigationRequest(
                    indicator_value="1.1.1.1",
                    indicator_type="ip",
                    initial_alert_id="ALERT-001"
                )
                investigation_res = await copilot.auto_investigate(invest_req)
                logger.info(f"\nAuto-Investigation:\n{investigation_res.model_dump_json(indent=2)}")

                # Test write_detection_rule
                rule_req = RuleGenerationRequest(
                    event_pattern={"event_type": "process.create", "process_name": "mimikatz.exe"},
                    rule_type="yara",
                    context_info="Detect credential dumping tools."
                )
                rule_res = await copilot.write_detection_rule(rule_req)
                logger.info(f"\nGenerated Rule:\n{rule_res.model_dump_json(indent=2)}")

                # Test generate_threat_report
                report_req = ThreatReportRequest(incident_id="INC-001", report_type="executive")
                report_res = await copilot.generate_threat_report(report_req)
                logger.info(f"\nThreat Report:\n{report_res.model_dump_json(indent=2)}")
        else:
            logger.info("LLM API keys configured. Running with live LLM (might incur costs/delays).")
            # You can run live tests here if API keys are set and you're aware of costs.
            # Example:
            # alert_req = AlertExplanationRequest(
            #     alert_title="Suspicious Login",
            #     alert_description="User 'jdoe' logged in from a new geographic location.",
            #     alert_context={"user": "jdoe", "source_ip": "203.0.113.45", "country": "Nigeria"}
            # )
            # explanation_res = await copilot.explain_alert(alert_req)
            # logger.info(f"\nLive Alert Explanation:\n{explanation_res.model_dump_json(indent=2)}")

    try:
        asyncio.run(run_example())
    except KeyboardInterrupt:
        logger.info("SOCCopilotService example stopped.")
