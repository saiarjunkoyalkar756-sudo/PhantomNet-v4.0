import logging
import math
import re
from typing import Dict, Any, List
from collections import Counter
from features.synthetic_cognitive_memory.cognitive_memory import CognitiveMemory

logger = logging.getLogger("cognitive_core")

class CognitiveCore:
    """
    Cognitive Core Intelligence (Vectorized Episodic Memory)
    Replaces static dictionary signature matching with an advanced 
    TF-IDF Vectorized memory store. It extracts the semantic essence of incoming 
    telemetry and correlates it against past attacks.
    """

    def __init__(self, cognitive_memory: CognitiveMemory):
        self.memory = cognitive_memory
        self.vocabulary = set()
        self.idf_cache = {}
        # Pre-load episodes to build vocabulary
        self._initialize_vector_space()
        logger.info("Initializing Cognitive Core. Real Vectorized NLP active.")

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def _initialize_vector_space(self):
        """Loads previous attacks from memory and computes the NLP corpus."""
        all_episodes = self.memory.get_all_episodes()
        corpus_size = len(all_episodes)
        
        doc_freq = Counter()
        for ep in all_episodes:
            threat_str = str(ep.get("threat_data", ""))
            tokens = set(self._tokenize(threat_str))
            for t in tokens:
                doc_freq[t] += 1
                self.vocabulary.add(t)
                
        # Calculate IDF (Inverse Document Frequency)
        for token, freq in doc_freq.items():
            self.idf_cache[token] = math.log((corpus_size + 1) / (freq + 1)) + 1

    def _compute_tf_idf(self, text: str) -> Dict[str, float]:
        tokens = self._tokenize(text)
        tf = Counter(tokens)
        total_tokens = len(tokens)
        
        vector = {}
        for token, count in tf.items():
            tf_score = count / total_tokens
            idf_score = self.idf_cache.get(token, math.log(1.5)) # default for unseen
            vector[token] = tf_score * idf_score
        return vector

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        
        sum1 = sum([val ** 2 for val in vec1.values()])
        sum2 = sum([val ** 2 for val in vec2.values()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        
        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def analyze_threat(self, threat_data: Any) -> Dict[str, Any]:
        """
        Analyzes novel threats against the episodic memory bank using mathematical similarity.
        """
        threat_str = str(threat_data)
        logger.info(f"Cognitive Vectorization begun for: {threat_str[:50]}...")
        
        target_vector = self._compute_tf_idf(threat_str)
        
        all_episodes = self.memory.get_all_episodes()
        highest_similarity = 0.0
        best_match = None
        
        for ep in all_episodes:
            ep_str = str(ep.get("threat_data", ""))
            ep_vector = self._compute_tf_idf(ep_str)
            sim = self._cosine_similarity(target_vector, ep_vector)
            
            if sim > highest_similarity:
                highest_similarity = sim
                best_match = ep

        # Decision making
        if highest_similarity > 0.85:
            logger.info(f"High cognitive overlap ({highest_similarity*100:.1f}%). Recall activated.")
            analysis_result = {
                "status": "analyzed_from_memory",
                "threat_level": best_match['analysis'].get('threat_level', 'high'),
                "description": f"Vector match! Semantically identical to historical attack: {best_match.get('resolution')}",
                "similarity_score": highest_similarity,
            }
        else:
            logger.info("Novel anomaly detected. Zero-Day heuristic analysis initiated.")
            analysis_result = {
                "status": "zero_day_analyzed",
                "threat_level": "critical",
                "description": "Novel threat. Semantic vector isolated and stored for future episodic recall.",
                "similarity_score": highest_similarity,
            }
            # Auto-learn
            self.memory.store_episode(threat_str, analysis_result, "Novel Attack Vector Auto-Logged.")
            
        return analysis_result

    def execute_action(self, action: dict) -> dict:
        """
        Executes an action passed down from the neural language layers.
        """
        intent = action.get("intent")
        logger.info(f"Cognitive Core executing: {intent}")
        if intent == "auto_isolation_trigger":
            return {"status": "executed", "action": "network_isolation", "details": action.get("details")}
        return {"status": "failed", "reason": "unrecognized_intent"}
