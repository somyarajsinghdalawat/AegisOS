from collections import defaultdict, deque
import time


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
            float(process["cpu"])
        )

        data["memory"].append(
            float(process["memory_mb"])
        )

        data["threads"].append(
            int(process["threads"])
        )

        data["timestamps"].append(
            time.time()
        )

    def get(self, pid):

        return self.history.get(pid)

    def remove(self, pid):

        if pid in self.history:
            del self.history[pid]

    def size(self):

        return len(self.history)

    def clear(self):

        self.history.clear()