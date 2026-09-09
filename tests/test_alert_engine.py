from ml.alert_engine import AlertEngine


def create_result(
    risk=70,
    status="ANOMALY"
):

    return {
        "pid": 1234,
        "status": status,
        "risk": risk,
        "score": -0.3,
        "level": "HIGH",

        "features": {
            "cpu_mean": 80,
            "cpu_max": 95,
            "cpu_std": 10,
            "cpu_recent": 85,

            "memory_mean": 1200,
            "memory_max": 1500,
            "memory_std": 100,
            "memory_recent": 1300,

            "threads_mean": 10,
            "threads_max": 20,
            "threads_recent": 15,

            "cpu_slope": 3,
            "memory_slope": 6,
            "thread_slope": 6,

            "cpu_change": 20,
            "memory_change": 100,
            "thread_change": 5,

            "cpu_volatility": 5,
            "memory_volatility": 10,

            "samples": 20
        }
    }


def test_anomaly_should_alert():

    engine = AlertEngine()

    result = create_result()

    assert engine.should_alert(
        result
    ) is True


def test_normal_should_not_alert():

    engine = AlertEngine()

    result = create_result(
        risk=70,
        status="NORMAL"
    )

    assert engine.should_alert(
        result
    ) is False


def test_low_risk_should_not_alert():

    engine = AlertEngine()

    result = create_result(
        risk=10
    )

    assert engine.should_alert(
        result
    ) is False


def test_cooldown():

    engine = AlertEngine()

    result = create_result()

    first = engine.should_alert(
        result
    )

    second = engine.should_alert(
        result
    )

    assert first is True

    assert second is False


def test_alert_creation():

    engine = AlertEngine()

    result = create_result()

    alert = engine.create_alert(
        result
    )

    assert alert["pid"] == 1234

    assert alert["status"] == "ANOMALY"

    assert alert["risk"] == 70

    assert len(
        alert["reasons"]
    ) > 0