import time
import numpy as np

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory

from ml.features import FeatureEngineer
from ml.model_trainer import ModelTrainer
from ml.model_evaluator import ModelEvaluator


SAMPLES = 40
PROCESS_LIMIT = 20
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
    "memory_volatility"
]


print()
print("AEGIS OS")
print("MODEL PERFORMANCE EVALUATION")
print("============================")
print()

monitor = ProcessMonitor()

history = ProcessHistory(
    max_length=HISTORY_LENGTH
)

print(
    f"Collecting {SAMPLES} independent samples..."
)

start_time = time.time()

for sample in range(SAMPLES):

    processes = monitor.get_processes(
        limit=PROCESS_LIMIT
    )

    for process in processes:
        history.update(process)

    print(
        f"Sample {sample + 1}/{SAMPLES}"
    )

    time.sleep(1)


collection_time = time.time() - start_time


# -----------------------------------------------------
# Feature extraction
# -----------------------------------------------------

feature_vectors = []

for pid in history.history:

    process_history = history.get(pid)

    features = FeatureEngineer.process_features(
        process_history
    )

    if features is None:
        continue

    vector = [
        features[name]
        for name in FEATURE_NAMES
    ]

    feature_vectors.append(vector)


print()
print(
    "Independent test profiles:",
    len(feature_vectors)
)


if len(feature_vectors) < 20:

    raise RuntimeError(
        "Not enough independent samples "
        "for evaluation."
    )


# -----------------------------------------------------
# Train / validation split
# -----------------------------------------------------

trainer = ModelTrainer(
    contamination=0.05
)

train_data, validation_data = (
    trainer.split_dataset(
        feature_vectors,
        validation_ratio=0.20
    )
)


print()
print("TRAINING / VALIDATION")
print("---------------------")
print(
    "Training samples   :",
    len(train_data)
)
print(
    "Validation samples :",
    len(validation_data)
)


# -----------------------------------------------------
# Train model
# -----------------------------------------------------

detector = trainer.train(
    train_data
)


# -----------------------------------------------------
# Evaluate validation data
# -----------------------------------------------------

evaluator = ModelEvaluator()

evaluation = evaluator.evaluate(
    detector,
    validation_data
)


print()
print("MODEL PERFORMANCE")
print("-----------------")

print(
    f"Validation samples : "
    f"{evaluation['samples']}"
)

print(
    f"Normal predictions : "
    f"{evaluation['normal']}"
)

print(
    f"Anomaly predictions: "
    f"{evaluation['anomaly']}"
)

print(
    f"Anomaly rate       : "
    f"{evaluation['anomaly_rate'] * 100:.2f}%"
)

print(
    f"Minimum score      : "
    f"{evaluation['min_score']:.6f}"
)

print(
    f"Maximum score      : "
    f"{evaluation['max_score']:.6f}"
)

print(
    f"Mean score         : "
    f"{evaluation['mean_score']:.6f}"
)

print(
    f"Detection time     : "
    f"{collection_time:.2f} seconds"
)

print()
print("============================")
print("Evaluation complete.")