import os
import time


PROCESS_NAME = "AegisOS-FaultSimulator"


def create_cpu_stress():
    """
    Continuously generate controlled CPU load.

    The simulator intentionally stays alive until AegisOS
    terminates it through the controlled self-healing path.
    """
    print(
        f"[FAULT SIMULATOR] {PROCESS_NAME} started",
        flush=True,
    )
    print(
        f"[FAULT SIMULATOR] PID: {os.getpid()}",
        flush=True,
    )
    print(
        "[FAULT SIMULATOR] Generating CPU anomaly.",
        flush=True,
    )
    print(
        "[FAULT SIMULATOR] Waiting for AegisOS self-healing...",
        flush=True,
    )

    while True:
        end = time.perf_counter() + 0.20

        while time.perf_counter() < end:
            x = 0
            for i in range(1_000_000):
                x += i * i

        time.sleep(0.05)


def main():
    try:
        create_cpu_stress()

    except KeyboardInterrupt:
        print(
            "[FAULT SIMULATOR] Stopped manually.",
            flush=True,
        )


if __name__ == "__main__":
    main()
