# plugins/anomaly_detector_ai/anomaly_entry.py
import json
import random
import time
import numpy as np
from sklearn.ensemble import IsolationForest # For a more realistic simulation

def analyze_event_for_anomaly(event_data: dict) -> dict:
    """
    Simulates AI analysis of an event for anomalies.
    """
    print(f"[{__name__}] Analyzing event data: {event_data.get('id', 'N/A')}")

    # Simulate some processing time
    time.sleep(random.uniform(0.1, 0.8))

    # For a simple simulation, we'll generate a random anomaly score
    # In a real scenario, this would involve feature extraction and a trained ML model
    anomaly_score = random.uniform(0.0, 1.0) # Threshold for anomaly
    is_anomaly = anomaly_score > 0.7 

    prediction_confidence = 1.0 - abs(0.5 - anomaly_score) * 2 # Higher confidence for scores closer to 0 or 1

    # Simulate a simple Isolation Forest for a more "AI" feel without actual training
    # This just generates a prediction based on some dummy data structure
    # This part is illustrative and doesn't genuinely train or use IsolationForest
    try:
        # Dummy data for IsolationForest prediction
        # In a real scenario, event_data would be converted into features
        dummy_features = np.array([
            random.uniform(0,1), random.uniform(0,1), random.uniform(0,1),
            event_data.get("severity", 0.5), event_data.get("frequency", 0.5)
        ]).reshape(1, -1)
        
        # A very simple, untuned model for illustration
        model = IsolationForest(random_state=42)
        # Dummy fit, never actually training on real data here
        model.fit(np.array([[0.5,0.5,0.5,0.5,0.5], [0.1,0.1,0.1,0.1,0.1], [0.9,0.9,0.9,0.9,0.9]]))
        
        # Isolation Forest outputs -1 for outliers and 1 for inliers
        if model.predict(dummy_features)[0] == -1:
            if not is_anomaly: # Bias towards anomaly if model "predicts" it
                anomaly_score = min(1.0, anomaly_score + 0.2)
                is_anomaly = True
        else:
            if is_anomaly: # Bias towards not anomaly if model "predicts" it
                anomaly_score = max(0.0, anomaly_score - 0.2)
                is_anomaly = False

    except Exception as e:
        print(f"[{__name__}] Warning: Could not simulate IsolationForest prediction: {e}")
        # Fallback to random score if ML simulation fails

    result = {
        "event_id": event_data.get("id", "N/A"),
        "timestamp": time.time(),
        "anomaly_score": round(anomaly_score, 3),
        "is_anomaly": is_anomaly,
        "prediction_confidence": round(prediction_confidence, 3),
        "suggested_action": "Investigate" if is_anomaly else "Monitor"
    }
    print(f"[{__name__}] Anomaly analysis completed for event: {result['event_id']}")
    return result

if __name__ == "__main__":
    # Example usage for local testing
    test_event = {
        "id": "event-123",
        "source_ip": "192.168.1.100",
        "destination_ip": "10.0.0.5",
        "port": 445,
        "protocol": "SMB",
        "severity": 0.8,
        "frequency": 0.9,
        "payload_size": 1024
    }

    print(f"--- Testing Anomaly Detector AI Plugin ---")
    analysis_output = analyze_event_for_anomaly(test_event)
    print(json.dumps(analysis_output, indent=2))
    print("---------------------------------------")

    test_event_low_risk = {
        "id": "event-124",
        "source_ip": "192.168.1.10",
        "destination_ip": "10.0.0.1",
        "port": 80,
        "protocol": "HTTP",
        "severity": 0.1,
        "frequency": 0.1,
        "payload_size": 200
    }
    print(f"\n--- Testing Anomaly Detector AI Plugin (Low Risk Event) ---")
    analysis_output_low_risk = analyze_event_for_anomaly(test_event_low_risk)
    print(json.dumps(analysis_output_low_risk, indent=2))
    print("---------------------------------------")
