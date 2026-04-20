# phantomnet_agent/analyzers/ml_analyzer.py
import os
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import make_pipeline
from .base import Analyzer

logger = logging.getLogger(__name__)

class MLAnalyzer(Analyzer):
    """
    Hybrid ML Analyzer:
    1. Supervised (Naive Bayes) for known attack signature classification.
    2. Unsupervised (Isolation Forest) for novel anomaly detection.
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500)
        self.signature_model = None
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self._initialize()

    def _initialize(self):
        data_path = os.path.join(os.path.dirname(__file__), "..", "attack_data.csv")
        try:
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                # Train Signature Model
                X = self.vectorizer.fit_transform(df["payload"])
                self.signature_model = MultinomialNB()
                self.signature_model.fit(X, df["type"])
                
                # Train Anomaly Detector (Baseline on 'trusted' or known data)
                # In a real scenario, we'd train this on clean traffic
                self.anomaly_detector.fit(X.toarray())
                logger.info("ML Models (NaiveBayes + IsolationForest) initialized and trained.")
            else:
                logger.warning(f"Attack data not found at {data_path}. ML analysis will be limited.")
        except Exception as e:
            logger.error(f"Failed to initialize ML models: {e}")

    def analyze(self, payload: str) -> Dict[str, Any]:
        """
        Analyzes a payload for both known attacks and anomalies.
        """
        if not self.signature_model or not payload:
            return {"prediction": "unknown", "anomaly_score": 0.0, "is_anomaly": False}

        try:
            X_vec = self.vectorizer.transform([payload]).toarray()
            
            # 1. Signature Prediction
            prediction = self.signature_model.predict(X_vec)[0]
            probs = self.signature_model.predict_proba(X_vec)[0]
            confidence = float(np.max(probs))

            # 2. Anomaly Detection
            # Isolation Forest returns -1 for anomalies and 1 for normal
            anomaly_val = self.anomaly_detector.predict(X_vec)[0]
            # decision_function returns the anomaly score (lower is more anomalous)
            anomaly_score = float(self.anomaly_detector.decision_function(X_vec)[0])
            
            is_anomaly = anomaly_val == -1

            return {
                "prediction": prediction,
                "confidence": confidence,
                "anomaly_score": anomaly_score,
                "is_anomaly": is_anomaly,
                "threat_level": "high" if is_anomaly or confidence > 0.8 else "low"
            }
        except Exception as e:
            logger.error(f"Error during ML analysis: {e}")
            return {"prediction": "error", "error": str(e)}

    def detect_numerical_anomaly(self, data: np.ndarray) -> bool:
        """
        Specialized method for detecting anomalies in numerical buffers 
        (e.g., connection spikes, process frequency).
        """
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        
        preds = self.anomaly_detector.predict(data)
        return bool(np.any(preds == -1))
