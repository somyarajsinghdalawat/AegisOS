import json
from pathlib import Path
from datetime import datetime


class ReportGenerator:

    RESULTS_PATH = Path(
        "evaluation/experiment_results.json"
    )

    REPORT_PATH = Path(
        "evaluation/evaluation_report.md"
    )

    def __init__(self, results_path=None):

        self.results_path = Path(
            results_path
            if results_path
            else self.RESULTS_PATH
        )

    def load_results(self):

        if not self.results_path.exists():
            raise FileNotFoundError(
                f"Results not found: {self.results_path}"
            )

        with open(
            self.results_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    def generate(self, output_path=None):

        data = self.load_results()

        metrics = data.get(
            "metrics",
            {}
        )

        experiment = data.get(
            "experiment",
            {}
        )

        if output_path is None:
            output_path = self.REPORT_PATH

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        report = f"""
# AegisOS Evaluation Report

## Experiment

**Name:** {experiment.get("name", "AegisOS")}

**Generated:** {datetime.now().isoformat()}

---

## Results

| Metric | Value |
|---|---:|
| Total observations | {metrics.get("total_observations", 0)} |
| Normal observations | {metrics.get("normal_observations", 0)} |
| Anomaly observations | {metrics.get("anomaly_observations", 0)} |
| High-risk observations | {metrics.get("high_risk_observations", 0)} |
| Critical observations | {metrics.get("critical_observations", 0)} |
| Anomaly rate | {metrics.get("anomaly_rate", 0)} |
| Average risk | {metrics.get("average_risk", 0)} |

---

## System

AegisOS continuously monitors process-level system behavior.

The monitored signals include:

- CPU usage
- Memory consumption
- Thread count
- Historical behavior
- Behavioral changes
- Machine-learning anomaly score
- Risk score

---

## Detection Pipeline

Process Monitoring
→ Historical Data
→ Feature Engineering
→ Standardization
→ Isolation Forest
→ Anomaly Detection
→ Risk Engine
→ Alert Engine
→ Recovery Policy
→ Safe Recovery
→ Verification
→ Incident Logging

---

## Interpretation

An anomaly indicates that observed process behavior differs from the
learned behavioral baseline.

An anomaly does not automatically mean that a process is malicious.

The risk engine combines behavioral signals and the machine-learning
result to produce a risk score.

---

## Current Evaluation

The automated test suite validates:

- Feature extraction
- Insufficient history handling
- Risk calculation
- Machine-learning model training
- Anomaly prediction
- Obvious anomaly detection
- Invalid feature dimensions
- Alert generation
- Alert cooldown
- Fault simulator availability

---

## Limitations

The current evaluation is an engineering experiment and should not be
interpreted as proof of malicious-process detection.

Legitimate applications can also behave unusually because of:

- Compilation
- Gaming
- Software updates
- Data processing
- Development workloads

Therefore:

Anomaly != Malware

---

## Future Evaluation

Future experiments should include:

- Larger datasets
- Labeled malicious processes
- Controlled attack simulations
- False-positive analysis
- False-negative analysis
- Precision
- Recall
- F1 score
- Detection latency
- Recovery success
- Verification success
- CPU overhead
- Memory overhead

---

## Conclusion

AegisOS provides an integrated process-monitoring and anomaly-detection
pipeline.

The system combines behavioral monitoring, feature engineering,
unsupervised machine learning, risk assessment, alert generation,
controlled recovery, verification, and incident logging.

Further evaluation is required before making claims about real-world
malware detection effectiveness.
"""

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                report.strip()
            )

        return output_path


if __name__ == "__main__":

    generator = ReportGenerator()

    try:

        path = generator.generate()

        print(
            f"Report generated: {path}"
        )

    except FileNotFoundError as exc:

        print(
            f"Error: {exc}"
        )