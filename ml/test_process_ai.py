import time

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory

from ml.features import FeatureEngineer
from ml.process_anomaly_detector import (
    ProcessAnomalyDetector
)
from ml.risk_engine import RiskEngine


# =====================================================
# Configuration
# =====================================================

SAMPLES = 30
PROCESS_LIMIT = 20


# =====================================================
# Initialize
# =====================================================

monitor = ProcessMonitor()

history_manager = ProcessHistory(
    max_length=30
)


print()
print("AEGIS OS")
print("Process AI Analysis")
print("===================")
print()

print(
    f"Collecting {SAMPLES} samples..."
)
print()


# =====================================================
# Collect process history
# =====================================================

for sample in range(SAMPLES):

    processes = monitor.get_processes(
        limit=PROCESS_LIMIT
    )

    for process in processes:

        history_manager.update(
            process
        )

    print(
        f"Sample {sample + 1}/{SAMPLES}"
    )

    time.sleep(1)


# =====================================================
# Feature extraction
# =====================================================

feature_names = [

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


feature_records = []


for pid in history_manager.history:

    history = (
        history_manager.get(pid)
    )

    features = (
        FeatureEngineer.process_features(
            history
        )
    )

    if features is None:
        continue

    feature_records.append({

        "pid": pid,

        "features": features
    })


print()
print(
    "Usable process profiles:",
    len(feature_records)
)


if len(feature_records) < 10:

    raise RuntimeError(
        "Not enough process profiles "
        "to train the AI model."
    )


# =====================================================
# Build feature matrix
# =====================================================

feature_vectors = []


for record in feature_records:

    features = record["features"]

    vector = [
        features[name]
        for name in feature_names
    ]

    feature_vectors.append(
        vector
    )


# =====================================================
# Train AI
# =====================================================

detector = ProcessAnomalyDetector()

detector.train(
    feature_vectors
)


risk_engine = RiskEngine()


# =====================================================
# Analyze
# =====================================================

print()
print(
    "PROCESS AI RESULTS"
)
print(
    "=================="
)


results = []


for record in feature_records:

    pid = record["pid"]

    features = record["features"]

    vector = [
        features[name]
        for name in feature_names
    ]

    prediction, anomaly_score = (
        detector.predict(
            vector
        )
    )

    risk_result = (
        risk_engine.calculate(
            features,
            anomaly_score,
            prediction
        )
    )

    if prediction == -1:
        ai_status = "ANOMALY"
    else:
        ai_status = "NORMAL"

    result = {

        "pid": pid,

        "status": ai_status,

        "score": anomaly_score,

        "risk": risk_result["risk"],

        "level": risk_result["level"],

        "features": features
    }

    results.append(result)


# =====================================================
# Sort by risk
# =====================================================

results.sort(
    key=lambda item: item["risk"],
    reverse=True
)


# =====================================================
# Display
# =====================================================

for result in results:

    features = result["features"]

    print()

    print(
        f"PID: {result['pid']}"
    )

    print(
        f"AI Status: {result['status']}"
    )

    print(
        f"Anomaly Score: "
        f"{result['score']:.4f}"
    )

    print(
        f"Risk Score: "
        f"{result['risk']:.0f}/100"
    )

    print(
        f"Risk Level: "
        f"{result['level']}"
    )

    print(
        f"CPU Mean: "
        f"{features['cpu_mean']:.2f}%"
    )

    print(
        f"CPU Max: "
        f"{features['cpu_max']:.2f}%"
    )

    print(
        f"CPU Slope: "
        f"{features['cpu_slope']:.4f}"
    )

    print(
        f"Memory Mean: "
        f"{features['memory_mean']:.2f} MB"
    )

    print(
        f"Memory Slope: "
        f"{features['memory_slope']:.4f}"
    )

    print(
        f"Thread Mean: "
        f"{features['threads_mean']:.2f}"
    )

    print(
        f"Thread Slope: "
        f"{features['thread_slope']:.4f}"
    )


print()
print("==================")
print("Analysis complete.")