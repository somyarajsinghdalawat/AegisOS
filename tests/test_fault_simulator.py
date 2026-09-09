import sys
from pathlib import Path


FAULT_SIMULATOR = (
    Path(__file__).parent /
    "fault_simulator.py"
)


def test_fault_simulator_exists():

    assert FAULT_SIMULATOR.exists()


def test_fault_simulator_importable():

    sys.path.insert(
        0,
        str(
            FAULT_SIMULATOR.parent
        )
    )

    import fault_simulator

    assert fault_simulator is not None