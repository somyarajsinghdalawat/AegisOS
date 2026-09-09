import time

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory

from ml.features import FeatureEngineer
from ml.risk_engine import RiskEngine
from ml.model_manager import ModelManager
from ml.alert_engine import AlertEngine
from ml.recovery_policy import RecoveryPolicyEngine

from recovery.safe_recovery import SafeRecoveryEngine
from recovery.verification import RecoveryVerification

from database.incident_logger import IncidentLogger


SAMPLE_INTERVAL = 1
PROCESS_LIMIT = 20
HISTORY_LENGTH = 30
MIN_SAMPLES = 10
DISPLAY_INTERVAL = 5
TRAINING_SAMPLES = 30

DRY_RUN = True


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


monitor = ProcessMonitor()

history_manager = ProcessHistory(
    max_length=HISTORY_LENGTH
)

feature_engineer = FeatureEngineer()

risk_engine = RiskEngine()

model_manager = ModelManager()

alert_engine = AlertEngine()

recovery_policy = RecoveryPolicyEngine()

recovery_engine = SafeRecoveryEngine(
    dry_run=DRY_RUN
)

recovery_verifier = RecoveryVerification(
    monitor
)

incident_logger = IncidentLogger()


def collect_training_data():

    print(
        f"Collecting {TRAINING_SAMPLES} samples..."
    )
    print()

    for sample_number in range(
        1,
        TRAINING_SAMPLES + 1
    ):

        print(
            f"Sample {sample_number}/{TRAINING_SAMPLES}",
            end="\r",
            flush=True
        )

        processes = monitor.get_processes(
            limit=PROCESS_LIMIT
        )

        for process in processes:
            history_manager.update(
                process
            )

        time.sleep(
            SAMPLE_INTERVAL
        )

    print()
    print()


def build_feature_vectors():

    feature_vectors = []

    for pid in list(
        history_manager.history.keys()
    ):

        history = history_manager.get(pid)

        if history is None:
            continue

        if len(history["cpu"]) < MIN_SAMPLES:
            continue

        try:

            features = (
                feature_engineer.process_features(
                    history
                )
            )

            if features is None:
                continue

            vector = [
                float(features[name])
                for name in FEATURE_NAMES
            ]

            feature_vectors.append(
                vector
            )

        except (
            ValueError,
            KeyError,
            ZeroDivisionError,
            TypeError
        ):
            continue

    return feature_vectors


def train_model():

    feature_vectors = (
        build_feature_vectors()
    )

    print(
        f"Usable process profiles: "
        f"{len(feature_vectors)}"
    )
    print()

    if len(feature_vectors) < 10:

        raise RuntimeError(
            "Not enough usable process profiles "
            "for training."
        )

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
    print()


def analyze_processes():

    processes = monitor.get_processes(
        limit=PROCESS_LIMIT
    )

    results = []

    for process in processes:

        pid = process["pid"]

        history_manager.update(
            process
        )

        history = history_manager.get(
            pid
        )

        if history is None:
            continue

        if len(history["cpu"]) < MIN_SAMPLES:
            continue

        try:

            features = (
                feature_engineer.process_features(
                    history
                )
            )

            if features is None:
                continue

            vector = [
                float(features[name])
                for name in FEATURE_NAMES
            ]

            prediction, anomaly_score = (
                model_manager.predict(
                    vector
                )
            )

            if prediction == -1:
                status = "ANOMALY"
            else:
                status = "NORMAL"

            risk_result = (
                risk_engine.calculate(
                    features,
                    anomaly_score,
                    prediction
                )
            )

            risk = risk_result["risk"]
            level = risk_result["level"]

            results.append(
                {
                    "pid": pid,
                    "process_name": process["name"],
                    "status": status,
                    "score": anomaly_score,
                    "risk": risk,
                    "level": level,
                    "features": features
                }
            )

        except (
            ValueError,
            KeyError,
            RuntimeError,
            ZeroDivisionError,
            TypeError
        ):
            continue

    return results


def process_alerts(results):

    for result in results:

        if not alert_engine.should_alert(
            result
        ):
            continue

        alert = (
            alert_engine.create_alert(
                result
            )
        )

        alert_engine.format_alert(
            alert
        )

        incident_id = (
            incident_logger.log_incident(

                pid=result["pid"],

                process_name=
                    result["process_name"],

                anomaly_score=
                    result["score"],

                risk_score=
                    result["risk"],

                risk_level=
                    result["level"],

                reasons=
                    alert["reasons"],

                action="ALERT",

                recovery_status=
                    "NOT_ATTEMPTED",

                recovery_verification=
                    "NOT_VERIFIED"
            )
        )

        persistent = True

        confidence = min(
            1.0,
            max(
                0.0,
                abs(
                    float(
                        result["score"]
                    )
                ) * 2
            )
        )

        controlled_test = (
            recovery_engine.is_controlled_process(
                result["pid"]
            )
        )

        policy = (
            recovery_policy.decide(

                result=result,

                persistent=persistent,

                confidence=confidence,

                controlled_test=
                    controlled_test
            )
        )

        print(
            f"[RECOVERY POLICY] "
            f"PID={result['pid']} "
            f"ACTION={policy['action']} "
            f"CLASS={policy['classification']}"
        )

        recovery_reason = (
            f"Risk={result['risk']:.0f}, "
            f"persistent={persistent}, "
            f"confidence={confidence:.2f}, "
            f"reason={policy['reason']}"
        )

        recovery_result = (
            recovery_engine.execute(

                policy,

                result["pid"],

                reason=recovery_reason
            )
        )

        verification_result = {
            "status": "NOT_VERIFIED"
        }

        if (
            recovery_result["action"]
            != "NONE"
        ):

            verification_result = (
                recovery_verifier.verify(

                    pid=result["pid"],

                    action=
                        recovery_result["action"]
                )
            )

        resolution_timestamp = None

        if (
            verification_result["status"]
            in (
                "SUCCESS",
                "PARTIAL",
                "FAILED"
            )
        ):

            resolution_timestamp = time.time()

        incident_logger.update_recovery(

            incident_id=incident_id,

            action=
                recovery_result["action"],

            recovery_status=
                recovery_result["status"],

            recovery_verification=
                verification_result["status"],

            resolution_timestamp=
                resolution_timestamp
        )

        if (
            recovery_result["status"]
            == "SUCCESS"
        ):

            recovery_policy.mark_recovery(
                result["pid"]
            )

        print(
            f"[RECOVERY RESULT] "
            f"PID={result['pid']} "
            f"STATUS={recovery_result['status']} "
            f"VERIFICATION="
            f"{verification_result['status']}"
        )


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

        cpu = features[
            "cpu_recent"
        ]

        memory = features[
            "memory_recent"
        ]

        threads = features[
            "threads_recent"
        ]

        print(
            f"{result['pid']:<8}"
            f"{result['status']:<10}"
            f"{result['risk']:<8.0f}"
            f"{result['level']:<10}"
            f"{cpu:<10.2f}"
            f"{memory:<12.2f}"
            f"{threads:<10.1f}"
        )

    print()


def realtime_monitor():

    print(
        "Starting real-time monitoring..."
    )
    print()

    print(
        "Press CTRL+C to stop."
    )
    print()

    last_display = 0

    try:

        while True:

            results = (
                analyze_processes()
            )

            process_alerts(
                results
            )

            current_time = time.time()

            if (
                current_time - last_display
                >= DISPLAY_INTERVAL
            ):

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
            "Stopping AegisOS "
            "real-time monitoring..."
        )

    finally:

        incident_logger.close()


def main():

    print()
    print("AEGIS OS")
    print("Process AI Model Training")
    print("=========================")
    print()

    collect_training_data()

    train_model()

    realtime_monitor()


if __name__ == "__main__":
    main()