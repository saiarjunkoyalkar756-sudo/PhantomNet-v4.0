import os
import importlib
import logging
from typing import Dict, Any, List, Optional

from phantomnet_agent.analyzers.base import Analyzer
# Import AI modules for integration
from backend_api.ai.neuro_symbolic_engine import NeuroSymbolicEngine
from backend_api.ai.risk_index_predictor import RiskIndexPredictor
from backend_api.ai.cyber_knowledge_graph import CyberKnowledgeGraph
from backend_api.ai.multimodal_threat_intel import MultimodalThreatIntel

# Import AgentState and AIAnalysisResult
from core.state import get_agent_state
from schemas.events import AIAnalysisResult

logger = logging.getLogger("phantomnet_agent.ai_analyzer")

class AIAnalyzer:
    """
    Orchestrates the AI reasoning pipeline, accepting normalized events and
    producing a comprehensive AIAnalysisResult.
    """
    def __init__(self):
        self.logger = logging.getLogger("phantomnet_agent.ai_analyzer")
        agent_state = get_agent_state() # Access agent state to check config
        self.safe_ai_mode = agent_state.config.agent.safe_ai_mode

        self.analyzers: List[Analyzer] = []
        self.neuro_symbolic_engine: Optional[NeuroSymbolicEngine] = None
        self.risk_index_predictor: Optional[RiskIndexPredictor] = None
        self.cyber_knowledge_graph: Optional[CyberKnowledgeGraph] = None
        self.multimodal_threat_intel: Optional[MultimodalThreatIntel] = None

        if self.safe_ai_mode:
            self.logger.warning("AIAnalyzer initialized in SAFE AI MODE. Deep AI models are simulated.")
        else:
            try:
                self.neuro_symbolic_engine = NeuroSymbolicEngine()
                self.risk_index_predictor = RiskIndexPredictor()
                self.cyber_knowledge_graph = CyberKnowledgeGraph()
                self.multimodal_threat_intel = MultimodalThreatIntel()
                self.logger.info("AI core modules initialized for full AI analysis.")
            except Exception as e:
                self.logger.error(f"Failed to initialize one or more AI core modules: {e}. Falling back to SAFE AI MODE.", exc_info=True)
                self.safe_ai_mode = True # Force safe mode if initialization fails

        self._load_analyzers()

    def _load_analyzers(self):
        """Loads basic analyzers from the 'analyzers' directory."""
        analyzers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyzers")
        for filename in os.listdir(analyzers_dir):
            if (
                filename.endswith(".py")
                and filename != "base.py"
                and not filename.startswith("__")
            ):
                module_name = f"phantomnet_agent.analyzers.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for item in dir(module):
                        obj = getattr(module, item)
                        if (
                            isinstance(obj, type)
                            and issubclass(obj, Analyzer)
                            and obj is not Analyzer
                        ):
                            self.analyzers.append(obj())
                except Exception as e:
                    self.logger.error(f"Failed to load analyzer {module_name}: {e}", exc_info=True)
        self.logger.info(f"Loaded {len(self.analyzers)} basic analyzers.")

    def _analyze_payload_with_analyzers(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Applies all loaded basic analyzers to the payload and returns their raw results.
        Each analyzer result should include 'attack_type' and optionally 'confidence'.
        If no analyzers yield results, returns a simulated anomaly.
        """
        results = []
        for analyzer in self.analyzers:
            try:
                result = analyzer.analyze(payload)
                if result:
                    if isinstance(result, dict):
                        results.append(result)
                    elif isinstance(result, str):
                        results.append({"attack_type": result, "confidence": 0.5})
                    else:
                        self.logger.warning(f"Analyzer {type(analyzer).__name__} returned unexpected type: {type(result)}")
            except Exception as e:
                self.logger.error(f"Error running analyzer {type(analyzer).__name__}: {e}", exc_info=True)
        
        if not results:
            results.append({
                "attack_type": "Simulated Anomaly",
                "confidence": 0.2,
                "details": "No specific analyzer results found; returning simulated anomaly score."
            })
        return results

    async def reason_on_threat(self, threat_event: Dict[str, Any]) -> AIAnalysisResult:
        """
        Orchestrates advanced AI reasoning based on a detected threat event.
        Returns a comprehensive AIAnalysisResult.
        """
        event_id = threat_event.get("event_id", "N/A")
        analysis_result = AIAnalysisResult(event_id=event_id, status="failed", reason="AI analysis not performed")

        if self.safe_ai_mode:
            analysis_result.status = "simulated"
            analysis_result.reason = "Operating in SAFE AI MODE. AI analysis is simulated."
            analysis_result.initial_analysis = self._analyze_payload_with_analyzers(threat_event)
            analysis_result.inferred_context = ["Simulated: Potential threat activity detected."]
            analysis_result.context_confidence = 0.5
            analysis_result.risk_score = 0.3 # Default simulated risk
            analysis_result.risk_factors = ["Simulated risk assessment due to SAFE AI MODE."]
            analysis_result.attributed_to = "Simulated Threat Actor"
            analysis_result.attribution_confidence = 0.1
            self.logger.info(f"AI analysis for event {event_id} simulated due to SAFE AI MODE.", extra={"result": analysis_result.model_dump()})
            return analysis_result

        # Proceed with full AI analysis if not in safe mode
        try:
            # Step 1: Initial analysis by basic analyzers
            analysis_result.initial_analysis = self._analyze_payload_with_analyzers(threat_event)

            # Step 2: Threat Context Inference and Confidence Scoring (via NeuroSymbolicEngine)
            context_inference_result = await self.neuro_symbolic_engine.infer_context(threat_event)
            analysis_result.inferred_context = context_inference_result.get("inferred_context", [])
            analysis_result.context_confidence = context_inference_result.get("confidence", 0.0)

            # Step 3: Multimodal Threat Intelligence Enrichment
            ti_enrichment_result = await self.multimodal_threat_intel.enrich_event(threat_event)
            analysis_result.ti_matches = ti_enrichment_result.get("ti_matches", [])
            analysis_result.matched_ttps = ti_enrichment_result.get("matched_ttps", [])

            # Step 4: Graph Enrichment (via CyberKnowledgeGraph)
            graph_enrichment_result = await self.cyber_knowledge_graph.enrich_event_with_graph_data(threat_event)
            analysis_result.graph_enrichment_findings = graph_enrichment_result.get("graph_enrichment_findings", [])

            # Step 5: Risk Index Prediction
            risk_prediction_result = await self.risk_index_predictor.predict_risk(threat_event)
            analysis_result.risk_score = risk_prediction_result.get("risk_score", 0.0)
            analysis_result.risk_factors = risk_prediction_result.get("risk_factors", [])

            # Step 6: Threat Attribution Reasoning (via NeuroSymbolicEngine)
            attribution_result = await self.neuro_symbolic_engine.perform_attribution_reasoning(threat_event)
            analysis_result.attributed_to = attribution_result.get("attributed_to", "Unknown")
            analysis_result.attribution_confidence = attribution_result.get("attribution_confidence", 0.0)

            analysis_result.status = "success"
            self.logger.info(f"Advanced AI analysis completed for threat event {event_id}.", extra={"result": analysis_result.model_dump()})

        except Exception as e:
            analysis_result.status = "failed"
            analysis_result.reason = f"An error occurred during full AI analysis: {e}"
            self.logger.error(f"Error during full AI analysis for event {event_id}: {e}. Returning failed analysis result.", exc_info=True)

        return analysis_result
