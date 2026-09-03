import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class ProcessAnomalyDetector:

    def __init__(self):

        self.scaler = StandardScaler()

        self.model = IsolationForest(
            n_estimators=200,
            contamination=0.10,
            random_state=42
        )

        self.trained = False

    def train(self, feature_vectors):

        if len(feature_vectors) < 10:

            raise ValueError(
                "At least 10 feature vectors "
                "are required."
            )

        matrix = np.asarray(
            feature_vectors,
            dtype=float
        )

        scaled = self.scaler.fit_transform(
            matrix
        )

        self.model.fit(
            scaled
        )

        self.trained = True

    def predict(self, feature_vector):

        if not self.trained:

            raise RuntimeError(
                "Model must be trained before prediction."
            )

        vector = np.asarray(
            feature_vector,
            dtype=float
        ).reshape(1, -1)

        scaled = self.scaler.transform(
            vector
        )

        prediction = self.model.predict(
            scaled
        )[0]

        raw_score = float(
            self.model.decision_function(
                scaled
            )[0]
        )

        return prediction, raw_score