from detection.process_history import ProcessHistory
from ml.features import FeatureEngineer


def create_history():

    history_manager = ProcessHistory(
        max_length=30
    )

    for i in range(15):

        process = {
            "pid": 1234,
            "name": "test_process",
            "status": "running",
            "cpu": float(10 + i),
            "memory_percent": 2.0,
            "memory_mb": float(100 + i),
            "threads": 5 + i
        }

        history_manager.update(process)

    return history_manager.get(1234)


def test_feature_extraction():

    history = create_history()

    features = FeatureEngineer.process_features(
        history
    )

    assert features is not None

    assert features["samples"] == 15

    assert features["cpu_mean"] > 0

    assert features["cpu_max"] >= features["cpu_mean"]

    assert features["memory_mean"] > 0

    assert features["threads_mean"] > 0


def test_insufficient_samples():

    history_manager = ProcessHistory(
        max_length=30
    )

    for _ in range(5):

        history_manager.update({
            "pid": 1,
            "name": "test",
            "status": "running",
            "cpu": 10,
            "memory_percent": 1,
            "memory_mb": 100,
            "threads": 5
        })

    history = history_manager.get(1)

    result = FeatureEngineer.process_features(
        history
    )

    assert result is None