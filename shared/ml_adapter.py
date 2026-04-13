# shared/ml_adapter.py

import logging
import os
import numpy as np # Import numpy
from typing import Dict, Any, Optional

from utils.logger import get_logger
from shared.platform_utils import SAFE_MODE, PLATFORM_INFO # Import platform_info for capabilities

logger = get_logger(__name__)

# --- Conditional Imports for ML Frameworks ---
# TensorFlow
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
    logger.info("TensorFlow available. Full ML model support enabled.")
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available. ML model will fallback to TFLite or Heuristics.")

# TensorFlow Lite
try:
    if not TENSORFLOW_AVAILABLE: # Try TFLite only if full TF isn't there
        import tflite_runtime.interpreter as tflite
        TFLITE_AVAILABLE = True
        logger.info("TensorFlow Lite available. Lightweight ML model support enabled.")
    else:
        TFLITE_AVAILABLE = False # No need for TFLite if full TF is there
except ImportError:
    TFLITE_AVAILABLE = False
    if not TENSORFLOW_AVAILABLE:
        logger.warning("TensorFlow Lite not available. ML model will fallback to Heuristics.")

class MLAdapter:
    """
    Provides a unified interface for ML predictions, adapting based on
    available ML frameworks (TensorFlow, TFLite) and platform capabilities.
    """
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.full_model = None
        self.tflite_interpreter = None
        self.current_ml_mode = "HEURISTICS" # Default fallback
        self.safe_mode = SAFE_MODE or PLATFORM_INFO.get("safe_mode", False)

        if self.safe_mode:
            logger.info("MLAdapter running in SAFE_MODE. Using Heuristics/Mock ML model.")
            self.current_ml_mode = "HEURISTICS_SAFE_MODE"
        elif TENSORFLOW_AVAILABLE and self.model_path:
            try:
                self.full_model = tf.keras.models.load_model(self.model_path)
                self.current_ml_mode = "TENSORFLOW_FULL"
                logger.info(f"Loaded full TensorFlow model from {self.model_path}.")
            except Exception as e:
                logger.error(f"Failed to load TensorFlow model from {self.model_path}: {e}")
                self._load_tflite_model() # Try TFLite as fallback
        elif TFLITE_AVAILABLE and self.model_path:
            self._load_tflite_model()
        else:
            logger.warning("No suitable ML model (TensorFlow or TFLite) loaded. Using Heuristics/Mock ML model.")

    def _load_tflite_model(self):
        """Attempts to load a TFLite model."""
        try:
            # Assuming a .tflite model for lightweight inference
            if self.model_path and self.model_path.endswith(".tflite"):
                self.tflite_interpreter = tflite.Interpreter(model_path=self.model_path)
                self.tflite_interpreter.allocate_tensors()
                self.current_ml_mode = "TENSORFLOW_LITE"
                logger.info(f"Loaded TensorFlow Lite model from {self.model_path}.")
            else:
                logger.warning("Model path is not a .tflite model. Cannot load TFLite model.")
        except Exception as e:
            logger.error(f"Failed to load TFLite model from {self.model_path}: {e}")

    def predict(self, input_data: Any) -> Dict[str, Any]:
        """
        Provides a prediction based on the current ML mode.
        Input_data should be a preprocessed format compatible with the model.
        """
        if self.safe_mode or self.current_ml_mode == "HEURISTICS_SAFE_MODE":
            logger.debug("MLAdapter: Predicting using heuristics (SAFE_MODE).")
            return self._predict_heuristics(input_data)
        elif self.current_ml_mode == "TENSORFLOW_FULL":
            logger.debug("MLAdapter: Predicting using full TensorFlow model.")
            return self._predict_tensorflow(input_data)
        elif self.current_ml_mode == "TENSORFLOW_LITE":
            logger.debug("MLAdapter: Predicting using TensorFlow Lite model.")
            return self._predict_tflite(input_data)
        else:
            logger.debug("MLAdapter: Predicting using heuristics (fallback).")
            return self._predict_heuristics(input_data)

    def _predict_tensorflow(self, input_data: Any) -> Dict[str, Any]:
        """Performs prediction using the full TensorFlow model."""
        if self.full_model:
            # Example: Assuming input_data is a numpy array
            prediction = self.full_model.predict(input_data)
            return {"prediction": prediction.tolist(), "mode": "tensorflow_full"}
        return {"prediction": [0.5], "mode": "tensorflow_full_failed"}

    def _predict_tflite(self, input_data: Any) -> Dict[str, Any]:
        """Performs prediction using the TensorFlow Lite interpreter."""
        if self.tflite_interpreter:
            input_details = self.tflite_interpreter.get_input_details()
            output_details = self.tflite_interpreter.get_output_details()
            
            # Assuming input_data is a numpy array, convert to appropriate type and shape
            self.tflite_interpreter.set_tensor(input_details[0]['index'], input_data.astype(input_details[0]['dtype']))
            self.tflite_interpreter.invoke()
            
            output_data = self.tflite_interpreter.get_tensor(output_details[0]['index'])
            return {"prediction": output_data.tolist(), "mode": "tensorflow_lite"}
        return {"prediction": [0.5], "mode": "tensorflow_lite_failed"}

    def _predict_heuristics(self, input_data: Any) -> Dict[str, Any]:
        """Performs prediction using simple heuristics or a mock."""
        # This is a mock implementation
        if isinstance(input_data, dict) and input_data.get("malicious_indicator"):
            return {"prediction": [0.9], "mode": "heuristics_malicious"}
        return {"prediction": [0.1], "mode": "heuristics_clean"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Running MLAdapter example...")
    
    # Mocking PLATFORM_INFO for testing different scenarios
    # Scenario 1: No ML libs available, use heuristics
    with patch('shared.platform_utils.TENSORFLOW_AVAILABLE', False), \
         patch('shared.platform_utils.TFLITE_AVAILABLE', False), \
         patch('shared.platform_utils.SAFE_MODE', False), \
         patch.dict(os.environ, {}, clear=True):
        ml_adapter_heuristics = MLAdapter()
        logger.info(f"ML Mode (Heuristics): {ml_adapter_heuristics.current_ml_mode}")
        prediction_heuristics = ml_adapter_heuristics.predict({"malicious_indicator": False})
        logger.info(f"Prediction (Heuristics): {prediction_heuristics}")
        assert prediction_heuristics["mode"] == "heuristics_clean"

    # Scenario 2: SAFE_MODE enabled, use heuristics
    with patch('shared.platform_utils.TENSORFLOW_AVAILABLE', True), \
         patch('shared.platform_utils.TFLITE_AVAILABLE', True), \
         patch('shared.platform_utils.SAFE_MODE', True), \
         patch.dict(os.environ, {"PHANTOMNET_SAFE_MODE": "true"}, clear=True):
        ml_adapter_safe = MLAdapter(model_path="dummy_model.keras") # Model path doesn't matter in SAFE_MODE
        logger.info(f"ML Mode (SAFE_MODE): {ml_adapter_safe.current_ml_mode}")
        prediction_safe = ml_adapter_safe.predict({"malicious_indicator": True})
        logger.info(f"Prediction (SAFE_MODE): {prediction_safe}")
        assert prediction_safe["mode"] == "heuristics_malicious"

    # Scenario 3: TensorFlow available (mock loading)
    # Mock TensorFlow's load_model and predict for this test
    class MockKerasModel:
        def predict(self, data):
            import numpy as np
            return np.array([[0.99]])
    with patch('shared.ml_adapter.TENSORFLOW_AVAILABLE', True), \
         patch('shared.ml_adapter.TFLITE_AVAILABLE', False), \
         patch('shared.ml_adapter.SAFE_MODE', False), \
         patch('tensorflow.keras.models.load_model', MagicMock(return_value=MockKerasModel())), \
         patch.dict(os.environ, {}, clear=True):
        ml_adapter_tf = MLAdapter(model_path="dummy_model.keras")
        logger.info(f"ML Mode (TensorFlow Full): {ml_adapter_tf.current_ml_mode}")
        import numpy as np
        prediction_tf = ml_adapter_tf.predict(np.array([[0.1, 0.2]]))
        logger.info(f"Prediction (TensorFlow Full): {prediction_tf}")
        assert prediction_tf["mode"] == "tensorflow_full"
        assert prediction_tf["prediction"] == [[0.99]]

    # Scenario 4: TFLite available (mock loading)
    # Mock tflite_runtime.interpreter for this test
    class MockTFLiteInterpreter:
        def __init__(self, model_path): pass
        def allocate_tensors(self): pass
        def get_input_details(self): return [{'index': 0, 'dtype': 'float32'}]
        def get_output_details(self): return [{'index': 0}]
        def set_tensor(self, index, data): pass
        def invoke(self): pass
        def get_tensor(self, index): return np.array([[0.8]])
    
    from unittest.mock import patch, MagicMock
    with patch('shared.ml_adapter.TENSORFLOW_AVAILABLE', False), \
         patch('shared.ml_adapter.TFLITE_AVAILABLE', True), \
         patch('shared.ml_adapter.SAFE_MODE', False), \
         patch('tflite_runtime.interpreter.Interpreter', MagicMock(return_value=MockTFLiteInterpreter("dummy.tflite"))), \
         patch.dict(os.environ, {}, clear=True):
        ml_adapter_tflite = MLAdapter(model_path="dummy_model.tflite")
        logger.info(f"ML Mode (TFLite): {ml_adapter_tflite.current_ml_mode}")
        import numpy as np
        prediction_tflite = ml_adapter_tflite.predict(np.array([[0.3, 0.4]]))
        logger.info(f"Prediction (TFLite): {prediction_tflite}")
        assert prediction_tflite["mode"] == "tensorflow_lite"
        assert prediction_tflite["prediction"] == [[0.8]]

    logger.info("MLAdapter example completed.")
