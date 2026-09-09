import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class ProcessAnomalyDetector:

    VERSION = "2.0"

    def __init__(
        self,
        n_estimators=300,
        contamination=0.05,
        random_state=42
    ):

        self.scaler = StandardScaler()

        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1
        )

        self.trained = False

        self.feature_count = None

        self.training_samples = 0

    def _validate_matrix(
        self,
        matrix
    ):

        matrix = np.asarray(
            matrix,
            dtype=float
        )

        if matrix.ndim != 2:

            raise ValueError(
                "Training data must be a 2D matrix."
            )

        if matrix.shape[0] < 10:

            raise ValueError(
                "At least 10 training samples are required."
            )

        if matrix.shape[1] < 1:

            raise ValueError(
                "Training data must contain features."
            )

        if not np.all(
            np.isfinite(matrix)
        ):

            raise ValueError(
                "Training data contains NaN or infinite values."
            )

        return matrix

    def train(
        self,
        feature_vectors
    ):

        matrix = self._validate_matrix(
            feature_vectors
        )

        self.feature_count = (
            matrix.shape[1]
        )

        scaled = self.scaler.fit_transform(
            matrix
        )

        self.model.fit(
            scaled
        )

        self.trained = True

        self.training_samples = (
            matrix.shape[0]
        )

    def predict(
        self,
        feature_vector
    ):

        if not self.trained:

            raise RuntimeError(
                "Model must be trained before prediction."
            )

        vector = np.asarray(
            feature_vector,
            dtype=float
        ).reshape(1, -1)

        if not np.all(
            np.isfinite(vector)
        ):

            raise ValueError(
                "Feature vector contains invalid values."
            )

        if (
            self.feature_count is not None
            and vector.shape[1] != self.feature_count
        ):

            raise ValueError(
                f"Expected {self.feature_count} features, "
                f"got {vector.shape[1]}."
            )

        scaled = self.scaler.transform(
            vector
        )

        prediction = int(
            self.model.predict(
                scaled
            )[0]
        )

        raw_score = float(
            self.model.decision_function(
                scaled
            )[0]
        )

        return prediction, raw_score

    def predict_many(
        self,
        feature_vectors
    ):

        if not self.trained:

            raise RuntimeError(
                "Model must be trained before prediction."
            )

        matrix = np.asarray(
            feature_vectors,
            dtype=float
        )

        if matrix.ndim != 2:

            raise ValueError(
                "Input must be a 2D matrix."
            )

        if not np.all(
            np.isfinite(matrix)
        ):

            raise ValueError(
                "Input contains invalid values."
            )

        if (
            self.feature_count is not None
            and matrix.shape[1] != self.feature_count
        ):

            raise ValueError(
                f"Expected {self.feature_count} features, "
                f"got {matrix.shape[1]}."
            )

        scaled = self.scaler.transform(
            matrix
        )

        predictions = (
            self.model.predict(
                scaled
            )
        )

        scores = (
            self.model.decision_function(
                scaled
            )
        )

        return (
            predictions,
            scores
        )

    def anomaly_strength(
        self,
        anomaly_score
    ):

        if anomaly_score >= 0:

            return 0.0

        strength = (
            -float(anomaly_score) / 0.5
        )

        return max(
            0.0,
            min(
                strength,
                1.0
            )
        )