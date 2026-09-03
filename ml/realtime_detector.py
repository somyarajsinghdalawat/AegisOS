import time

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory

from ml.features import FeatureEngineer
from ml.risk_engine import RiskEngine
from ml.model_manager import ModelManager


# =====================================================
# CONFIGURATION
# =====================================================

SAMPLE_INTERVAL = 1

PROCESS_LIMIT = 20

HISTORY_LENGTH = 30

MIN_SAMPLES = 10

# How often results are displayed
DISPLAY_INTERVAL = 5


# =====================================================
# FEATURE CONFIGURATION
# =====================================================

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


# =====================================================
# INITIALIZE
# =====================================================

monitor = ProcessMonitor()

history_manager = ProcessHistory(
    max_length=HISTORY_LENGTH
)

risk_engine = RiskEngine()

model_manager = ModelManager()


# =====================================================
# COLLECT TRAINING DATA
# =====================================================

def collect_training_data():

    print()
    print("AEGIS OS")
    print("Process AI Model Training")
    print("=========================")
    print()

    print(
        f"Collecting {HISTORY_LENGTH} samples..."
    )

    print()

    for sample in range(HISTORY_LENGTH):

        processes = monitor.get_processes(
            limit=PROCESS_LIMIT
        )

        for process in processes:

            history_manager.update(
                process
            )

        print(
            f"Sample {sample + 1}/{HISTORY_LENGTH}"
        )

        time.sleep(
            SAMPLE_INTERVAL
        )


# =====================================================
# BUILD FEATURE VECTORS
# =====================================================

def build_feature_vectors():

    feature_records = []

    for pid in history_manager.history:

        history = history_manager.get(
            pid
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

    if len(feature_records) < MIN_SAMPLES:

        raise RuntimeError(
            "Not enough process profiles "
            "to train the AI model."
        )

    feature_vectors = []

    for record in feature_records:

        features = record["features"]

        vector = [

            features[name]

            for name in FEATURE_NAMES
        ]

        feature_vectors.append(
            vector
        )

    return feature_records, feature_vectors


# =====================================================
# INITIAL TRAINING
# =====================================================

def train_model():

    collect_training_data()

    (
        feature_records,
        feature_vectors
    ) = build_feature_vectors()

    print()

    print(
        "Usable process profiles:",
        len(feature_records)
    )

    print()

    print(
        "Training process anomaly model..."
    )

    model_manager.train(
        feature_vectors
    )

    model_manager.save()

    print(
        "Training complete."
    )

    return feature_records


# =====================================================
# ANALYZE CURRENT PROCESSES
# =====================================================

def analyze_processes():

    results = []

    for pid in history_manager.history:

        history = history_manager.get(
            pid
        )

        features = (
            FeatureEngineer.process_features(
                history
            )
        )

        if features is None:
            continue

        vector = [

            features[name]

            for name in FEATURE_NAMES
        ]

        prediction, anomaly_score = (
            model_manager.predict(
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

        results.append({

            "pid": pid,

            "status": ai_status,

            "score": anomaly_score,

            "risk": risk_result["risk"],

            "level": risk_result["level"],

            "features": features
        })

    results.sort(
        key=lambda item: item["risk"],
        reverse=True
    )

    return results


# =====================================================
# DISPLAY RESULTS
# =====================================================

def display_results(results):

    print()
    print("AEGIS OS")
    print("REAL-TIME PROCESS AI")
    print("====================")
    print()

    print(
        f"{'PID':<8}"
        f"{'AI':<10}"
        f"{'Risk':<8}"
        f"{'Level':<10}"
        f"{'CPU':<10}"
        f"{'Memory':<12}"
        f"{'Threads':<10}"
    )

    print("-" * 70)

    for result in results:

        features = result["features"]

        print(

            f"{result['pid']:<8}"

            f"{result['status']:<10}"

            f"{result['risk']:<8.0f}"

            f"{result['level']:<10}"

            f"{features['cpu_mean']:<10.2f}"

            f"{features['memory_mean']:<12.2f}"

            f"{features['threads_mean']:<10.1f}"
        )


# =====================================================
# REAL-TIME MONITOR
# =====================================================

def realtime_monitor():

    print()
    print("Starting real-time monitoring...")
    print()
    print(
        "Press CTRL+C to stop."
    )
    print()

    last_display = 0

    while True:

        try:

            # -----------------------------------------
            # Collect current processes
            # -----------------------------------------

            processes = monitor.get_processes(
                limit=PROCESS_LIMIT
            )

            # -----------------------------------------
            # Update process history
            # -----------------------------------------

            for process in processes:

                history_manager.update(
                    process
                )

            # -----------------------------------------
            # Display periodically
            # -----------------------------------------

            current_time = time.time()

            if (
                current_time - last_display
                >= DISPLAY_INTERVAL
            ):

                results = analyze_processes()

                display_results(
                    results
                )

                last_display = current_time

            time.sleep(
                SAMPLE_INTERVAL
            )

        except KeyboardInterrupt:

            print()
            print(
                "Stopping Aegis OS monitoring..."
            )

            break

        except Exception as error:

            print()
            print(
                "Monitoring error:",
                error
            )

            time.sleep(2)


# =====================================================
# MAIN
# =====================================================

def main():

    try:

        # ---------------------------------------------
        # Train model
        # ---------------------------------------------

        train_model()

        # ---------------------------------------------
        # Continue monitoring
        # ---------------------------------------------

        realtime_monitor()

    except KeyboardInterrupt:

        print()
        print(
            "Aegis OS stopped."
        )


if __name__ == "__main__":

    main()