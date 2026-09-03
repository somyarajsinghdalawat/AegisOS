import time

from config.config import (
    CPU_WARNING_THRESHOLD,
    CPU_CRITICAL_THRESHOLD,
    CPU_CRITICAL_DURATION,
    MEMORY_GROWTH_WARNING_MB,
    MEMORY_GROWTH_CRITICAL_MB,
    THREAD_GROWTH_WARNING,
    THREAD_GROWTH_CRITICAL
)


class FaultDetector:

    def __init__(self):
        self.cpu_high_since = {}
        self.last_incident = {}

    def allow_incident(self, key):
        now = time.time()
        previous = self.last_incident.get(key)

        if previous is None:
            self.last_incident[key] = now
            return True

        if now - previous >= 30:
            self.last_incident[key] = now
            return True

        return False

    def detect(self, process, history):
        incidents = []

        pid = process["pid"]
        name = process["name"]

        cpu = process["cpu"]
        memory = process["memory_mb"]
        threads = process["threads"]

        current_time = time.time()

        # CPU detection
        if cpu >= CPU_CRITICAL_THRESHOLD:
            if pid not in self.cpu_high_since:
                self.cpu_high_since[pid] = current_time

            duration = current_time - self.cpu_high_since[pid]

            if duration >= CPU_CRITICAL_DURATION:
                if self.allow_incident(f"{pid}_CPU_RUNAWAY"):
                    incidents.append({
                        "type": "CPU_RUNAWAY",
                        "pid": pid,
                        "process": name,
                        "severity": "CRITICAL",
                        "score": min(100, cpu),
                        "message": f"{name} has sustained high CPU usage."
                    })

        elif cpu < CPU_WARNING_THRESHOLD:
            self.cpu_high_since.pop(pid, None)

        # Memory and Thread history-based detection
        if history:
            # Memory growth detection
            memory_history = list(history["memory"])

            if len(memory_history) >= 5:
                memory_growth = memory_history[-1] - memory_history[0]

                if memory_growth >= MEMORY_GROWTH_CRITICAL_MB:
                    if self.allow_incident(f"{pid}_MEMORY_LEAK"):
                        incidents.append({
                            "type": "MEMORY_LEAK",
                            "pid": pid,
                            "process": name,
                            "severity": "CRITICAL",
                            "score": min(100, 50 + memory_growth),
                            "message": f"{name} shows rapid memory growth."
                        })

                elif memory_growth >= MEMORY_GROWTH_WARNING_MB:
                    if self.allow_incident(f"{pid}_MEMORY_GROWTH"):
                        incidents.append({
                            "type": "MEMORY_GROWTH",
                            "pid": pid,
                            "process": name,
                            "severity": "WARNING",
                            "score": min(80, 30 + memory_growth),
                            "message": f"{name} shows abnormal memory growth."
                        })

            # Thread detection
            thread_history = list(history["threads"])

            if len(thread_history) >= 5:
                thread_growth = thread_history[-1] - thread_history[0]

                if thread_growth >= THREAD_GROWTH_CRITICAL:
                    if self.allow_incident(f"{pid}_THREAD_EXPLOSION"):
                        incidents.append({
                            "type": "THREAD_EXPLOSION",
                            "pid": pid,
                            "process": name,
                            "severity": "CRITICAL",
                            "score": 90,
                            "message": f"{name} has abnormal thread growth."
                        })

                elif thread_growth >= THREAD_GROWTH_WARNING:
                    if self.allow_incident(f"{pid}_THREAD_GROWTH"):
                        incidents.append({
                            "type": "THREAD_GROWTH",
                            "pid": pid,
                            "process": name,
                            "severity": "WARNING",
                            "score": 70,
                            "message": f"{name} shows increasing thread count."
                        })

        return incidents
