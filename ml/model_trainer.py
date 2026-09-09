from pathlib import Path

import numpy as np

from ml.process_anomaly_detector import (
    ProcessAnomalyDetector
)


class ModelTrainer:

    MODEL_PATH = Path(
        "ml/models/process_anomaly_model.pkl"
    )

    def __init__(
        self,
        contamination=0.05
    ):

        self.contamination = contamination

    def split_dataset(
        self,
        feature_vectors,
        validation_ratio=0.20
    ):

        matrix = np.asarray(
            feature_vectors,
            dtype=float
        )

        if matrix.ndim != 2:

            raise ValueError(
                "Dataset must be a 2D matrix."
            )

        if len(matrix) < 20:

            raise ValueError(
                "At least 20 samples are required "
                "for train/validation split."
            )

        if not 0 < validation_ratio < 1:

            raise ValueError(
                "validation_ratio must be between 0 and 1."
            )

        split_index = int(
            len(matrix) *
            (1.0 - validation_ratio)
        )

        split_index = max(
            10,
            min(
                split_index,
                len(matrix) - 1
            )
        )

        train = matrix[
            :split_index
        ]

        validation = matrix[
            split_index:
        ]

        return train, validation

    def train(
        self,
        feature_vectors
    ):

        detector = ProcessAnomalyDetector(
            n_estimators=300,
            contamination=self.contamination,
            random_state=42
        )

        detector.train(
            feature_vectors
        )

        return detector

    def train_with_validation(
        self,
        feature_vectors,
        validation_ratio=0.20
    ):

        train_data, validation_data = (
            self.split_dataset(
                feature_vectors,
                validation_ratio
            )
        )

        detector = self.train(
            train_data
        )

        predictions, scores = (
            detector.predict_many(
                validation_data
            )
        )

        anomaly_count = int(
            np.sum(
                predictions == -1
            )
        )

        normal_count = int(
            np.sum(
                predictions == 1
            )
        )

        validation_size = len(
            validation_data
        )

        anomaly_rate = (
            anomaly_count /
            validation_size
        )

        result = {
            "detector": detector,
            "train_samples": len(
                train_data
            ),
            "validation_samples": validation_size,
            "validation_anomalies": anomaly_count,
            "validation_normal": normal_count,
            "validation_anomaly_rate": round(
                anomaly_rate,
                4
            ),
            "validation_min_score": float(
                np.min(scores)
            ),
            "validation_max_score": float(
                np.max(scores)
            ),
            "validation_mean_score": float(
                np.mean(scores)
            )
        }

        return result