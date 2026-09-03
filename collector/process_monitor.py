import psutil


class ProcessMonitor:

    def get_processes(self, limit=15):

        processes = []

        cpu_count = psutil.cpu_count(logical=True) or 1

        for process in psutil.process_iter(
            [
                "pid",
                "name",
                "status",
                "cpu_percent",
                "memory_percent",
                "memory_info",
                "num_threads"
            ]
        ):

            try:

                info = process.info

                pid = info.get("pid")

                # Ignore Windows PID 0.
                if pid == 0:
                    continue

                memory_info = info.get("memory_info")

                memory_mb = 0.0

                if memory_info:
                    memory_mb = (
                        memory_info.rss
                        / (1024 * 1024)
                    )

                raw_cpu = (
                    info.get("cpu_percent", 0.0)
                    or 0.0
                )

                # Normalize CPU to total-machine 0-100%.
                cpu = raw_cpu / cpu_count

                cpu = max(
                    0.0,
                    min(cpu, 100.0)
                )

                memory_percent = (
                    info.get("memory_percent", 0.0)
                    or 0.0
                )

                threads = (
                    info.get("num_threads", 0)
                    or 0
                )

                processes.append({
                    "pid": pid,
                    "name": (
                        info.get("name")
                        or "Unknown"
                    ),
                    "status": (
                        info.get("status")
                        or "unknown"
                    ),
                    "cpu": cpu,
                    "memory_percent": memory_percent,
                    "memory_mb": memory_mb,
                    "threads": threads
                })

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess
            ):
                continue

        processes.sort(
            key=lambda process: process["cpu"],
            reverse=True
        )

        return processes[:limit]