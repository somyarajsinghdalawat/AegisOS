import time


class RecoveryVerification:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"

    def __init__(self, process_monitor):
        self.process_monitor = process_monitor

    def process_exists(self, pid):
        try:
            import psutil

            process = psutil.Process(int(pid))
            return process.is_running()

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            return False

    def get_process_metrics(self, pid):
        try:
            import psutil

            process = psutil.Process(int(pid))

            with process.oneshot():
                cpu = process.cpu_percent(interval=0.1)
                memory = process.memory_info().rss / (1024 * 1024)
                threads = process.num_threads()

            return {
                "pid": int(pid),
                "cpu": float(cpu),
                "memory_mb": float(memory),
                "threads": int(threads)
            }

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            return None

    def verify_termination(self, pid):
        time.sleep(1)

        alive = self.process_exists(pid)

        if not alive:
            return {
                "status": self.SUCCESS,
                "process_alive": False,
                "anomaly_removed": True,
                "message": "Process is no longer running."
            }

        metrics = self.get_process_metrics(pid)

        return {
            "status": self.FAILED,
            "process_alive": True,
            "anomaly_removed": False,
            "metrics": metrics,
            "message": "Process is still running."
        }

    def verify_monitoring(self, pid, previous_metrics=None):
        current_metrics = self.get_process_metrics(pid)

        if current_metrics is None:
            return {
                "status": self.PARTIAL,
                "process_alive": False,
                "anomaly_removed": False,
                "message": "Process disappeared during verification."
            }

        if previous_metrics is None:
            return {
                "status": self.PARTIAL,
                "process_alive": True,
                "anomaly_removed": False,
                "metrics": current_metrics,
                "message": "No previous metrics available."
            }

        cpu_change = (
            current_metrics["cpu"] -
            previous_metrics["cpu"]
        )

        memory_change = (
            current_metrics["memory_mb"] -
            previous_metrics["memory_mb"]
        )

        if cpu_change < 0 and memory_change <= 0:
            status = self.SUCCESS
            anomaly_removed = True

        elif cpu_change < 0 or memory_change <= 0:
            status = self.PARTIAL
            anomaly_removed = True

        else:
            status = self.FAILED
            anomaly_removed = False

        return {
            "status": status,
            "process_alive": True,
            "anomaly_removed": anomaly_removed,
            "metrics": current_metrics,
            "cpu_change": cpu_change,
            "memory_change": memory_change,
            "message": "Post-recovery metrics evaluated."
        }

    def verify(self, pid, action, previous_metrics=None):
        if action == "TERMINATE":
            return self.verify_termination(pid)

        return self.verify_monitoring(
            pid,
            previous_metrics=previous_metrics
        )