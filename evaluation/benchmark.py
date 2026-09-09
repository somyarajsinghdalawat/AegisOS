import time
from pathlib import Path
from datetime import datetime

import psutil


class SystemBenchmark:

    def __init__(self):

        self.results = []

    def snapshot(self):

        memory = psutil.virtual_memory()

        return {
            "timestamp": datetime.now().isoformat(),

            "cpu_percent": float(
                psutil.cpu_percent(
                    interval=0.2
                )
            ),

            "memory_percent": float(
                memory.percent
            ),

            "memory_used_mb": round(
                memory.used / (1024 * 1024),
                2
            ),

            "memory_available_mb": round(
                memory.available / (1024 * 1024),
                2
            ),

            "process_count": len(
                psutil.pids()
            )
        }

    def run(
        self,
        duration=30,
        interval=1
    ):

        self.results.clear()

        start = time.time()

        while (
            time.time() - start
            < duration
        ):

            self.results.append(
                self.snapshot()
            )

            time.sleep(
                interval
            )

        return self.results

    def summary(self):

        if not self.results:

            return {}

        cpu_values = [
            item["cpu_percent"]
            for item in self.results
        ]

        memory_values = [
            item["memory_percent"]
            for item in self.results
        ]

        process_values = [
            item["process_count"]
            for item in self.results
        ]

        elapsed = (
            self.results[-1]["timestamp"]
        )

        return {
            "samples": len(
                self.results
            ),

            "cpu_average": round(
                sum(cpu_values)
                / len(cpu_values),
                2
            ),

            "cpu_max": round(
                max(cpu_values),
                2
            ),

            "memory_average": round(
                sum(memory_values)
                / len(memory_values),
                2
            ),

            "memory_max": round(
                max(memory_values),
                2
            ),

            "process_average": round(
                sum(process_values)
                / len(process_values),
                2
            ),

            "process_max": max(
                process_values
            ),

            "last_timestamp": elapsed
        }

    def save_csv(
        self,
        path="evaluation/system_benchmark.csv"
    ):

        if not self.results:

            raise ValueError(
                "No benchmark results available."
            )

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        columns = [
            "timestamp",
            "cpu_percent",
            "memory_percent",
            "memory_used_mb",
            "memory_available_mb",
            "process_count"
        ]

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                ",".join(columns)
                + "\n"
            )

            for result in self.results:

                file.write(
                    ",".join(
                        str(
                            result[column]
                        )
                        for column in columns
                    )
                    + "\n"
                )

        return path


if __name__ == "__main__":

    benchmark = SystemBenchmark()

    print(
        "Running AegisOS system benchmark..."
    )

    benchmark.run(
        duration=30,
        interval=1
    )

    print()
    print(
        "Benchmark Summary"
    )
    print(
        "=" * 40
    )

    summary = benchmark.summary()

    for key, value in summary.items():

        print(
            f"{key}: {value}"
        )

    path = benchmark.save_csv()

    print()
    print(
        f"Results saved to: {path}"
    )