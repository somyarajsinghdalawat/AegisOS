import json
import time
from pathlib import Path
from datetime import datetime

import psutil

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory
from ml.features import FeatureEngineer
from ml.model_manager import ModelManager
from ml.risk_engine import RiskEngine


class ExperimentRunner:

    RESULTS_PATH = Path(
        "evaluation/experiment_results.json"
    )

    FEATURE_NAMES = [
        "cpu_mean",
        "cpu_max",
        "cpu_std",
        "cpu_recent",

        "memory_mean",
        "memory_max",
        "memory_std",
        "memory_recent",

        "threads_mean",
        "threads_max",
        "threads_recent",

        "cpu_slope",
        "memory_slope",
        "thread_slope",

        "cpu_change",
        "memory_change",
        "thread_change",

        "cpu_volatility",
        "memory_volatility"
    ]

    def __init__(self):

        self.monitor = ProcessMonitor()

        self.history = ProcessHistory(
            max_length=30
        )

        self.feature_engineer = (
            FeatureEngineer()
        )

        self.model_manager = (
            ModelManager()
        )

        self.risk_engine = (
            RiskEngine()
        )

        self.results = []

    def load_model(self):

        self.model_manager.load()

    def vector_from_features(
        self,
        features
    ):

        return [
            features[name]
            for name in self.FEATURE_NAMES
        ]

    def collect_baseline(
        self,
        duration=30,
        interval=1
    ):

        start = time.time()

        while (
            time.time() - start
            < duration
        ):

            processes = (
                self.monitor.get_processes(
                    limit=20
                )
            )

            for process in processes:

                self.history.update(
                    process
                )

            time.sleep(
                interval
            )

    def analyze_once(self):

        processes = (
            self.monitor.get_processes(
                limit=20
            )
        )

        results = []

        for process in processes:

            pid = process["pid"]

            self.history.update(
                process
            )

            history = (
                self.history.get(pid)
            )

            if history is None:
                continue

            features = (
                self.feature_engineer
                .process_features(history)
            )

            if features is None:
                continue

            vector = (
                self.vector_from_features(
                    features
                )
            )

            prediction, score = (
                self.model_manager.predict(
                    vector
                )
            )

            risk = (
                self.risk_engine.calculate(
                    features,
                    score,
                    prediction
                )
            )

            result = {
                "timestamp":
                    datetime.now().isoformat(),

                "pid":
                    pid,

                "name":
                    process["name"],

                "prediction":
                    int(prediction),

                "status":
                    (
                        "ANOMALY"
                        if prediction == -1
                        else "NORMAL"
                    ),

                "score":
                    float(score),

                "risk":
                    float(risk["risk"]),

                "level":
                    risk["level"],

                "cpu":
                    float(process["cpu"]),

                "memory_mb":
                    float(process["memory_mb"]),

                "threads":
                    int(process["threads"])
            }

            results.append(
                result
            )

        return results

    def run(
        self,
        duration=60,
        interval=1
    ):

        if not self.model_manager.trained:

            self.load_model()

        self.results.clear()

        start = time.time()

        while (
            time.time() - start
            < duration
        ):

            results = self.analyze_once()

            self.results.extend(
                results
            )

            time.sleep(
                interval
            )

        return self.results

    def calculate_metrics(self):

        if not self.results:

            return {}

        total = len(
            self.results
        )

        anomalies = sum(
            1
            for result in self.results
            if result["status"] == "ANOMALY"
        )

        high_risk = sum(
            1
            for result in self.results
            if result["risk"] >= 60
        )

        critical = sum(
            1
            for result in self.results
            if result["risk"] >= 80
        )

        normal = total - anomalies

        anomaly_rate = (
            anomalies / total
            if total
            else 0
        )

        average_risk = (
            sum(
                result["risk"]
                for result in self.results
            )
            / total
        )

        return {
            "total_observations":
                total,

            "normal_observations":
                normal,

            "anomaly_observations":
                anomalies,

            "high_risk_observations":
                high_risk,

            "critical_observations":
                critical,

            "anomaly_rate":
                round(
                    anomaly_rate,
                    4
                ),

            "average_risk":
                round(
                    average_risk,
                    2
                )
        }

    def save_results(
        self,
        path=None
    ):

        if path is None:

            path = self.RESULTS_PATH

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        output = {
            "experiment": {
                "name":
                    "AegisOS Process Anomaly Detection",

                "timestamp":
                    datetime.now().isoformat()
            },

            "metrics":
                self.calculate_metrics(),

            "observations":
                self.results
        }

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                output,
                file,
                indent=4
            )

        return path


if __name__ == "__main__":

    runner = ExperimentRunner()

    print(
        "Loading AegisOS ML model..."
    )

    runner.load_model()

    print(
        "Running experiment..."
    )

    runner.run(
        duration=30,
        interval=1
    )

    metrics = (
        runner.calculate_metrics()
    )

    print()
    print(
        "Experiment Results"
    )
    print(
        "=" * 40
    )

    for key, value in metrics.items():

        print(
            f"{key}: {value}"
        )

    path = runner.save_results()

    print()
    print(
        f"Results saved to: {path}"
    )