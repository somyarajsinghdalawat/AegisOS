import psutil


class ProcessMonitor:

    def get_processes(self, limit=15):

        processes = []

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
                memory_info = info.get("memory_info")

                memory_mb = 0

                if memory_info:
                    memory_mb = memory_info.rss / (1024 * 1024)

                processes.append({
                    "pid": info["pid"],
                    "name": info["name"] or "Unknown",
                    "status": info["status"],
                    "cpu": info["cpu_percent"] or 0,
                    "memory_percent": info["memory_percent"] or 0,
                    "memory_mb": memory_mb,
                    "threads": info["num_threads"] or 0
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