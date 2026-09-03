import numpy as np


class FeatureEngineer:

    @staticmethod
    def process_features(history):

        if not history:
            return None

        cpu = np.asarray(
            history["cpu"],
            dtype=float
        )

        memory = np.asarray(
            history["memory"],
            dtype=float
        )

        threads = np.asarray(
            history["threads"],
            dtype=float
        )

        timestamps = np.asarray(
            history["timestamps"],
            dtype=float
        )

        sample_count = len(cpu)

        # We need enough observations
        # before calculating behavioral trends.
        if sample_count < 10:
            return None

        # ------------------------------------------------
        # CPU
        # ------------------------------------------------

        cpu_mean = float(np.mean(cpu))
        cpu_max = float(np.max(cpu))
        cpu_std = float(np.std(cpu))

        cpu_recent = float(
            np.mean(cpu[-5:])
        )

        # ------------------------------------------------
        # MEMORY
        # ------------------------------------------------

        memory_mean = float(
            np.mean(memory)
        )

        memory_max = float(
            np.max(memory)
        )

        memory_std = float(
            np.std(memory)
        )

        memory_recent = float(
            np.mean(memory[-5:])
        )

        # ------------------------------------------------
        # THREADS
        # ------------------------------------------------

        threads_mean = float(
            np.mean(threads)
        )

        threads_max = float(
            np.max(threads)
        )

        threads_recent = float(
            np.mean(threads[-5:])
        )

        # ------------------------------------------------
        # Trends
        # ------------------------------------------------

        elapsed = (
            timestamps[-1]
            - timestamps[0]
        )

        if elapsed <= 0:
            elapsed = 1.0

        cpu_slope = float(
            (cpu[-1] - cpu[0])
            / elapsed
        )

        memory_slope = float(
            (memory[-1] - memory[0])
            / elapsed
        )

        thread_slope = float(
            (threads[-1] - threads[0])
            / elapsed
        )

        # ------------------------------------------------
        # Recent change
        # ------------------------------------------------

        cpu_change = float(
            cpu[-1] - cpu[0]
        )

        memory_change = float(
            memory[-1] - memory[0]
        )

        thread_change = float(
            threads[-1] - threads[0]
        )

        # ------------------------------------------------
        # Volatility
        # ------------------------------------------------

        if len(cpu) > 1:
            cpu_volatility = float(
                np.mean(
                    np.abs(
                        np.diff(cpu)
                    )
                )
            )
        else:
            cpu_volatility = 0.0

        if len(memory) > 1:
            memory_volatility = float(
                np.mean(
                    np.abs(
                        np.diff(memory)
                    )
                )
            )
        else:
            memory_volatility = 0.0

        return {

            "cpu_mean": cpu_mean,
            "cpu_max": cpu_max,
            "cpu_std": cpu_std,
            "cpu_recent": cpu_recent,

            "memory_mean": memory_mean,
            "memory_max": memory_max,
            "memory_std": memory_std,
            "memory_recent": memory_recent,

            "threads_mean": threads_mean,
            "threads_max": threads_max,
            "threads_recent": threads_recent,

            "cpu_slope": cpu_slope,
            "memory_slope": memory_slope,
            "thread_slope": thread_slope,

            "cpu_change": cpu_change,
            "memory_change": memory_change,
            "thread_change": thread_change,

            "cpu_volatility": cpu_volatility,
            "memory_volatility": memory_volatility,

            "samples": sample_count
        }