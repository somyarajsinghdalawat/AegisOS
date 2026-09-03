from pathlib import Path
import joblib

from ml.process_anomaly_detector import ProcessAnomalyDetector


class ModelManager:

    MODEL_PATH = Path("ml/models/process_anomaly_model.pkl")

    def __init__(self):

        self.detector = ProcessAnomalyDetector()

    # =================================================
    # TRAIN
    # =================================================

    def train(self, feature_vectors):

        if not feature_vectors:
            raise ValueError(
                "No feature vectors available for training."
            )

        self.detector.train(
            feature_vectors
        )

    # =================================================
    # SAVE
    # =================================================

    def save(self):

        self.MODEL_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        joblib.dump(
            self.detector,
            self.MODEL_PATH
        )

        print(
            f"Model saved to: {self.MODEL_PATH}"
        )

    # =================================================
    # LOAD
    # =================================================

    def load(self):

        if not self.MODEL_PATH.exists():

            raise FileNotFoundError(
                f"Model not found: {self.MODEL_PATH}"
            )

        self.detector = joblib.load(
            self.MODEL_PATH
        )

        print(
            f"Model loaded from: {self.MODEL_PATH}"
        )

    # =================================================
    # PREDICT
    # =================================================

    def predict(self, vector):

        return self.detector.predict(
            vector
        )