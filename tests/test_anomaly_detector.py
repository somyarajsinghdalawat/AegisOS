import numpy as np

from ml.process_anomaly_detector import (
    ProcessAnomalyDetector
)


def create_training_data():

    rng = np.random.default_rng(42)

    return rng.normal(
        loc=0,
        scale=1,
        size=(50, 5)
    )


def test_model_training():

    data = create_training_data()

    detector = ProcessAnomalyDetector(
        contamination=0.05
    )

    detector.train(
        data
    )

    assert detector.trained is True

    assert detector.feature_count == 5

    assert detector.training_samples == 50


def test_prediction():

    data = create_training_data()

    detector = ProcessAnomalyDetector(
        contamination=0.05
    )

    detector.train(
        data
    )

    prediction, score = detector.predict(
        data[0]
    )

    assert prediction in (
        -1,
        1
    )

    assert isinstance(
        score,
        float
    )


def test_obvious_anomaly():

    data = create_training_data()

    detector = ProcessAnomalyDetector(
        contamination=0.05
    )

    detector.train(
        data
    )

    anomaly = np.array([
        100,
        100,
        100,
        100,
        100
    ])

    prediction, score = detector.predict(
        anomaly
    )

    assert prediction == -1

    assert score < 0


def test_invalid_feature_count():

    data = create_training_data()

    detector = ProcessAnomalyDetector()

    detector.train(
        data
    )

    try:

        detector.predict([
            1,
            2
        ])

        assert False

    except ValueError:

        assert True