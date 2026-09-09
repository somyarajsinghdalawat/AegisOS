from pathlib import Path

import joblib

from ml.process_anomaly_detector import (
    ProcessAnomalyDetector
)


class ModelManager:

    MODEL_PATH = Path(
        "ml/models/process_anomaly_model.pkl"
    )

    def __init__(self):

        self.detector = (
            ProcessAnomalyDetector()
        )

    def train(
        self,
        feature_vectors
    ):

        if not feature_vectors:

            raise ValueError(
                "No feature vectors available for training."
            )

        self.detector.train(
            feature_vectors
        )

    def train_and_save(
        self,
        feature_vectors
    ):

        self.train(
            feature_vectors
        )

        self.save()

    def save(
        self,
        path=None
    ):

        if path is None:

            path = self.MODEL_PATH

        path = Path(
            path
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        joblib.dump(
            self.detector,
            path
        )

        print(
            f"Model saved to: {path}"
        )

    def load(
        self,
        path=None
    ):

        if path is None:

            path = self.MODEL_PATH

        path = Path(
            path
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Model not found: {path}"
            )

        self.detector = joblib.load(
            path
        )

        print(
            f"Model loaded from: {path}"
        )

    def predict(
        self,
        vector
    ):

        return self.detector.predict(
            vector
        )

    def predict_many(
        self,
        vectors
    ):

        return self.detector.predict_many(
            vectors
        )

    @property
    def trained(self):

        return self.detector.trained

    @property
    def feature_count(self):

        return self.detector.feature_count

    @property
    def training_samples(self):

        return self.detector.training_samples