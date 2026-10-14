import os
import sys
import time
import subprocess

import psutil
import matplotlib.pyplot as plt


SAMPLES = 20
INTERVAL = 1

RESULT_DIR = os.path.join("ml", "results")
os.makedirs(RESULT_DIR, exist_ok=True)


def start_cpu_fault():
    """Start the fault simulator and return the actual CPU-worker PID."""

    simulator = subprocess.Popen(
        [sys.executable, "-u", "tests/fault_simulator.py", "cpu"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    print("Starting controlled CPU fault...")

    # Give the simulator time to create its worker.
    time.sleep(2)

    parent = psutil.Process(simulator.pid)

    worker = None

    for _ in range(10):
        children = parent.children(recursive=True)

        candidates = []

        for child in children:
            try:
                if child.is_running():
                    cpu = child.cpu_percent(interval=0.2)
                    candidates.append((cpu, child))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            worker = candidates[0][1]
            break

        time.sleep(0.5)

    if worker is None:
        print("ERROR: Could not find CPU fault worker.")
        simulator.terminate()
        return None, None

    print(f"Simulator PID: {simulator.pid}")
    print(f"CPU fault worker PID: {worker.pid}")

    return simulator, worker.pid


def collect_data(pid):
    """Collect CPU, memory and CPU-derived risk over time."""

    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        print("ERROR: Fault process not found.")
        return [], [], [], []

    # Initialize CPU measurement.
    process.cpu_percent(interval=None)

    times = []
    cpu_values = []
    memory_values = []
    risk_values = []

    print("\nCollecting fault data...")

    for i in range(SAMPLES):
        if not process.is_running():
            print("Fault process stopped.")
            break

        try:
            cpu = process.cpu_percent(interval=1)
            memory = process.memory_info().rss / (1024 * 1024)

            # Keep CPU within normal percentage range.
            cpu = max(0.0, min(cpu, 100.0))

            # Risk score based on CPU behaviour.
            if cpu >= 90:
                risk = 95
            elif cpu >= 75:
                risk = 85
            elif cpu >= 60:
                risk = 70
            elif cpu >= 40:
                risk = 55
            elif cpu >= 20:
                risk = 35
            else:
                risk = 15

            times.append(i + 1)
            cpu_values.append(cpu)
            memory_values.append(memory)
            risk_values.append(risk)

            print(
                f"Sample {i + 1}/{SAMPLES} | "
                f"CPU={cpu:.2f}% | "
                f"Memory={memory:.2f} MB | "
                f"Risk={risk}"
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            break

    return times, cpu_values, memory_values, risk_values


def save_graph(x, y, xlabel, ylabel, title, filename):
    path = os.path.join(RESULT_DIR, filename)

    plt.figure(figsize=(10, 5))
    plt.plot(x, y, marker="o")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()

    print(f"Saved: {path}")


def main():

    print("=" * 50)
    print("AEGIS OS - FAULT PERFORMANCE GRAPHS")
    print("=" * 50)

    simulator, worker_pid = start_cpu_fault()

    if worker_pid is None:
        return

    try:
        times, cpu, memory, risk = collect_data(worker_pid)

        if not times:
            print("No data collected.")
            return

        save_graph(
            times,
            cpu,
            "Time (samples)",
            "CPU Usage (%)",
            "CPU Usage During Controlled CPU Fault",
            "cpu_vs_time.png"
        )

        save_graph(
            times,
            memory,
            "Time (samples)",
            "Memory Usage (MB)",
            "Memory Usage During Controlled CPU Fault",
            "memory_vs_time.png"
        )

        save_graph(
            times,
            risk,
            "Time (samples)",
            "Risk Score",
            "Risk Score During Controlled CPU Fault",
            "risk_vs_time.png"
        )

        print("\nGRAPH GENERATION COMPLETE")

    finally:
        try:
            worker = psutil.Process(worker_pid)
            if worker.is_running():
                worker.terminate()
                worker.wait(timeout=3)
        except Exception:
            pass

        try:
            if simulator.poll() is None:
                simulator.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    main()