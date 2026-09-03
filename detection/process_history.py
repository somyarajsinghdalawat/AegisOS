from collections import defaultdict, deque


class ProcessHistory:

    def __init__(self, max_length=30):

        self.max_length = max_length

        self.history = defaultdict(
            lambda: {
                "cpu": deque(maxlen=max_length),
                "memory": deque(maxlen=max_length),
                "threads": deque(maxlen=max_length),
                "timestamps": deque(maxlen=max_length)
            }
        )

    def update(self, process):

        pid = process["pid"]

        data = self.history[pid]

        data["cpu"].append(
            process["cpu"]
        )

        data["memory"].append(
            process["memory_mb"]
        )

        data["threads"].append(
            process["threads"]
        )

        import time

        data["timestamps"].append(
            time.time()
        )

    def get(self, pid):

        return self.history.get(pid)

    def remove(self, pid):

        if pid in self.history:
            del self.history[pid]