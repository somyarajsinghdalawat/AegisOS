from ml.risk_engine import RiskEngine


def normal_features():

    return {
        "cpu_mean": 5,
        "cpu_max": 10,
        "cpu_std": 2,
        "cpu_recent": 5,

        "memory_mean": 100,
        "memory_max": 150,
        "memory_std": 10,
        "memory_recent": 100,

        "threads_mean": 5,
        "threads_max": 7,
        "threads_recent": 5,

        "cpu_slope": 0,
        "memory_slope": 0,
        "thread_slope": 0,

        "cpu_change": 0,
        "memory_change": 0,
        "thread_change": 0,

        "cpu_volatility": 0,
        "memory_volatility": 0,

        "samples": 20
    }


def critical_features():

    return {
        "cpu_mean": 95,
        "cpu_max": 100,
        "cpu_std": 5,
        "cpu_recent": 95,

        "memory_mean": 2000,
        "memory_max": 3000,
        "memory_std": 100,
        "memory_recent": 2000,

        "threads_mean": 100,
        "threads_max": 200,
        "threads_recent": 150,

        "cpu_slope": 10,
        "memory_slope": 20,
        "thread_slope": 15,

        "cpu_change": 50,
        "memory_change": 1000,
        "thread_change": 100,

        "cpu_volatility": 10,
        "memory_volatility": 50,

        "samples": 20
    }


def test_normal_risk():

    engine = RiskEngine()

    result = engine.calculate(
        normal_features(),
        0.2,
        1
    )

    assert result["risk"] < 20

    assert result["level"] == "NORMAL"


def test_critical_risk():

    engine = RiskEngine()

    result = engine.calculate(
        critical_features(),
        -0.5,
        -1
    )

    assert result["risk"] >= 80

    assert result["level"] == "CRITICAL"