import sys
import time


def normal_mode():

    print("Running NORMAL mode")
    print("PID:", __import__("os").getpid())

    while True:

        # Small amount of normal work.
        total = 0

        for i in range(10000):
            total += i

        time.sleep(0.2)


def cpu_mode():

    print("Running CPU STRESS mode")
    print("PID:", __import__("os").getpid())

    while True:

        # Deliberately perform CPU-intensive work.
        total = 0

        for i in range(5_000_000):
            total += i * i


def memory_mode():

    print("Running MEMORY GROWTH mode")
    print("PID:", __import__("os").getpid())

    memory_blocks = []

    while True:

        # Allocate approximately 10 MB.
        block = bytearray(
            10 * 1024 * 1024
        )

        memory_blocks.append(
            block
        )

        print(
            "Allocated:",
            len(memory_blocks) * 10,
            "MB"
        )

        time.sleep(2)


def main():

    if len(sys.argv) < 2:

        print()
        print("Usage:")
        print(
            "python tests/fault_simulator.py normal"
        )
        print(
            "python tests/fault_simulator.py cpu"
        )
        print(
            "python tests/fault_simulator.py memory"
        )

        return

    mode = sys.argv[1].lower()

    if mode == "normal":

        normal_mode()

    elif mode == "cpu":

        cpu_mode()

    elif mode == "memory":

        memory_mode()

    else:

        print(
            "Unknown mode:",
            mode
        )


if __name__ == "__main__":
    main()