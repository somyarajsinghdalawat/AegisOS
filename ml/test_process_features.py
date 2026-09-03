import time

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory
from ml.features import FeatureEngineer


monitor = ProcessMonitor()

history_manager = ProcessHistory(
    max_length=30
)

print("Collecting process data...")

for sample in range(10):

    processes = monitor.get_processes(
        limit=15
    )

    for process in processes:

        history_manager.update(
            process
        )

    print(
        f"Sample {sample + 1}/10 collected"
    )

    # Match the dashboard's approximately
    # one-second monitoring interval.
    time.sleep(1)


print(
    "\nTracked processes:",
    history_manager.size()
)

print(
    "\nProcess features"
)

print(
    "================"
)

for pid in list(
    history_manager.history.keys()
)[:5]:

    history = history_manager.get(
        pid
    )

    features = (
        FeatureEngineer.process_features(
            history
        )
    )

    if features:

        print(
            f"\nPID: {pid}"
        )

        for name, value in features.items():

            if isinstance(value, float):

                print(
                    f"{name}: {value:.4f}"
                )

            else:

                print(
                    f"{name}: {value}"
                )