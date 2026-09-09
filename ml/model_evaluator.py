import numpy as np


class ModelEvaluator:

    @staticmethod
    def evaluate(
        detector,
        feature_vectors
    ):

        matrix = np.asarray(
            feature_vectors,
            dtype=float
        )

        if matrix.ndim != 2:

            raise ValueError(
                "Feature vectors must be a 2D matrix."
            )

        predictions, scores = (
            detector.predict_many(
                matrix
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

        total = len(
            predictions
        )

        anomaly_rate = (
            anomaly_count / total
            if total
            else 0.0
        )

        return {
            "samples": total,
            "normal": normal_count,
            "anomaly": anomaly_count,
            "anomaly_rate": round(
                anomaly_rate,
                4
            ),
            "min_score": round(
                float(np.min(scores)),
                6
            ) if total else 0.0,
            "max_score": round(
                float(np.max(scores)),
                6
            ) if total else 0.0,
            "mean_score": round(
                float(np.mean(scores)),
                6
            ) if total else 0.0
        }

    @staticmethod
    def evaluate_against_expected(
        detector,
        normal_samples,
        anomaly_samples
    ):

        normal_matrix = np.asarray(
            normal_samples,
            dtype=float
        )

        anomaly_matrix = np.asarray(
            anomaly_samples,
            dtype=float
        )

        normal_predictions, _ = (
            detector.predict_many(
                normal_matrix
            )
        )

        anomaly_predictions, _ = (
            detector.predict_many(
                anomaly_matrix
            )
        )

        normal_detection_rate = float(
            np.mean(
                normal_predictions == 1
            )
        )

        anomaly_detection_rate = float(
            np.mean(
                anomaly_predictions == -1
            )
        )

        return {
            "normal_detection_rate":
                round(
                    normal_detection_rate,
                    4
                ),

            "anomaly_detection_rate":
                round(
                    anomaly_detection_rate,
                    4
                ),

            "normal_samples":
                len(normal_matrix),

            "anomaly_samples":
                len(anomaly_matrix)
        }