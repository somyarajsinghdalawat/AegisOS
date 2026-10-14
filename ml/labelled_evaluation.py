import sys
import time
import subprocess
import re

import numpy as np
import psutil

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory
from ml.features import FeatureEngineer
from ml.model_trainer import ModelTrainer


SAMPLES = 30
PROCESS_LIMIT = 20
FAULT_SAMPLES = 20
HISTORY_LENGTH = 30

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
    "memory_volatility",
]


def make_vector(features):
    return [
        features[name]
        for name in FEATURE_NAMES
    ]


def collect_normal_profiles():

    print()
    print("STEP 1: COLLECTING NORMAL TRAINING DATA")
    print("----------------------------------------")

    monitor = ProcessMonitor()
    history = ProcessHistory(
        max_length=HISTORY_LENGTH
    )

    for i in range(SAMPLES):

        processes = monitor.get_processes(
            limit=PROCESS_LIMIT
        )

        for process in processes:
            history.update(process)

        print(
            f"Normal sample {i + 1}/{SAMPLES}"
        )

        time.sleep(1)

    vectors = []

    for pid in history.history:

        process_history = history.get(pid)

        features = FeatureEngineer.process_features(
            process_history
        )

        if features is None:
            continue

        vectors.append(
            make_vector(features)
        )

    return vectors


def collect_normal_test_profiles():

    print()
    print("STEP 2: COLLECTING SEPARATE NORMAL TEST DATA")
    print("--------------------------------------------")

    monitor = ProcessMonitor()
    history = ProcessHistory(
        max_length=HISTORY_LENGTH
    )

    for i in range(SAMPLES):

        processes = monitor.get_processes(
            limit=PROCESS_LIMIT
        )

        for process in processes:
            history.update(process)

        print(
            f"Normal test sample {i + 1}/{SAMPLES}"
        )

        time.sleep(1)

    vectors = []

    for pid in history.history:

        process_history = history.get(pid)

        features = FeatureEngineer.process_features(
            process_history
        )

        if features is None:
            continue

        vectors.append(
            make_vector(features)
        )

    return vectors


def start_cpu_fault():

    print()
    print("STEP 3: STARTING CONTROLLED CPU FAULT")
    print("--------------------------------------")

    command = [
        sys.executable,
        "-u",
        "tests/fault_simulator.py",
        "cpu",
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    pid = None

    deadline = time.time() + 10

    while time.time() < deadline:

        line = process.stdout.readline()

        if not line:
            continue

        print(
            "[FAULT]",
            line.strip()
        )

        match = re.search(
            r"PID:\s*(\d+)",
            line
        )

        if match:

            pid = int(
                match.group(1)
            )

            break

    if pid is None:

        process.terminate()

        raise RuntimeError(
            "Could not obtain fault simulator PID."
        )

    print(
        f"Controlled fault PID: {pid}"
    )

    return process, pid


def collect_fault_profile(pid):

    print()
    print("Collecting CPU fault behaviour...")
    print("--------------------------------")

    history = ProcessHistory(
        max_length=HISTORY_LENGTH
    )

    for i in range(FAULT_SAMPLES):

        try:

            process = psutil.Process(pid)

            cpu = process.cpu_percent(
                interval=0.2
            )

            memory_info = process.memory_info()

            memory_mb = (
                memory_info.rss /
                (1024 * 1024)
            )

            threads = process.num_threads()

            sample = {
                "pid": pid,
                "name": process.name(),
                "status": process.status(),
                "cpu": cpu,
                "memory_percent": process.memory_percent(),
                "memory_mb": memory_mb,
                "threads": threads,
            }

            history.update(sample)

            print(
                f"Fault sample {i + 1}/{FAULT_SAMPLES} "
                f"CPU={cpu:.2f}% "
                f"Memory={memory_mb:.2f}MB "
                f"Threads={threads}"
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):

            break

        time.sleep(1)

    features = FeatureEngineer.process_features(
        history.get(pid)
    )

    if features is None:

        raise RuntimeError(
            "Could not generate features "
            "from CPU fault process."
        )

    return make_vector(features)


def main():

    print()
    print("AEGIS OS")
    print("LABELLED MODEL PERFORMANCE EVALUATION")
    print("======================================")
    print()

    # -----------------------------------------
    # Training data
    # -----------------------------------------

    training_vectors = (
        collect_normal_profiles()
    )

    print()
    print(
        "Normal training profiles:",
        len(training_vectors)
    )

    if len(training_vectors) < 20:

        raise RuntimeError(
            "Not enough training profiles."
        )

    trainer = ModelTrainer(
        contamination=0.05
    )

    detector = trainer.train(
        training_vectors
    )

    print()
    print("Model trained using NORMAL behaviour.")

    # -----------------------------------------
    # Separate normal test data
    # -----------------------------------------

    normal_test_vectors = (
        collect_normal_test_profiles()
    )

    print()
    print(
        "Normal test profiles:",
        len(normal_test_vectors)
    )

    # -----------------------------------------
    # Controlled anomaly
    # -----------------------------------------

    fault_process = None

    try:

        fault_process, fault_pid = (
            start_cpu_fault()
        )

        anomaly_vector = (
            collect_fault_profile(
                fault_pid
            )
        )

    finally:

        if fault_process is not None:

            fault_process.terminate()

            try:
                fault_process.wait(
                    timeout=3
                )
            except subprocess.TimeoutExpired:
                fault_process.kill()

    # -----------------------------------------
    # Build labelled test set
    # -----------------------------------------

    X_test = (
        normal_test_vectors +
        [anomaly_vector]
    )

    y_true = (
        [0] * len(normal_test_vectors) +
        [1]
    )

    predictions, scores = (
        detector.predict_many(
            np.asarray(
                X_test,
                dtype=float
            )
        )
    )

    # Isolation Forest:
    # 1  = normal
    # -1 = anomaly

    y_pred = [
        1 if prediction == -1 else 0
        for prediction in predictions
    ]

    # -----------------------------------------
    # Metrics
    # -----------------------------------------

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    )

    tn, fp, fn, tp = (
        cm.ravel()
    )

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0.0
    )

    # -----------------------------------------
    # Display
    # -----------------------------------------

    print()
    print("======================================")
    print("AEGIS OS PERFORMANCE RESULTS")
    print("======================================")

    print(
        f"Training samples       : "
        f"{len(training_vectors)}"
    )

    print(
        f"Normal test samples    : "
        f"{len(normal_test_vectors)}"
    )

    print(
        "Anomaly test samples   : 1"
    )

    print()
    print(
        f"Accuracy               : "
        f"{accuracy * 100:.2f}%"
    )

    print(
        f"Precision              : "
        f"{precision * 100:.2f}%"
    )

    print(
        f"Recall                 : "
        f"{recall * 100:.2f}%"
    )

    print(
        f"F1 Score               : "
        f"{f1 * 100:.2f}%"
    )

    print(
        f"False Positive Rate    : "
        f"{false_positive_rate * 100:.2f}%"
    )

    print()
    print("CONFUSION MATRIX")
    print("----------------")

    print(
        "                 Predicted"
    )

    print(
        "              Normal  Anomaly"
    )

    print(
        f"Actual Normal  {tn:6d}  {fp:7d}"
    )

    print(
        f"Actual Anomaly {fn:6d}  {tp:7d}"
    )

    print()
    print(
        "Detection convention:"
    )

    print(
        "0 = Normal"
    )

    print(
        "1 = Anomaly"
    )

    print()
    print(
        "Evaluation complete."
    )


if __name__ == "__main__":
    main()