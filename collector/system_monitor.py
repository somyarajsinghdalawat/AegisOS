import psutil
import platform
import time


class SystemMonitor:

    def __init__(self):
        self.boot_time = psutil.boot_time()

    def get_os(self):
        return platform.system()

    def get_cpu(self):
        return psutil.cpu_percent(interval=None)

    def get_memory(self):
        memory = psutil.virtual_memory()

        return {
            "total": memory.total,
            "used": memory.used,
            "available": memory.available,
            "percent": memory.percent
        }

    def get_disk(self):
        disk = psutil.disk_usage("/")

        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }

    def get_network(self):
        network = psutil.net_io_counters()

        return {
            "sent": network.bytes_sent,
            "received": network.bytes_recv
        }

    def get_uptime(self):
        return time.time() - self.boot_time

    def get_snapshot(self):

        memory = self.get_memory()
        disk = self.get_disk()
        network = self.get_network()

        return {
            "timestamp": time.time(),
            "os": self.get_os(),
            "cpu": self.get_cpu(),
            "memory_percent": memory["percent"],
            "memory_used": memory["used"],
            "memory_total": memory["total"],
            "disk_percent": disk["percent"],
            "disk_used": disk["used"],
            "disk_total": disk["total"],
            "network_sent": network["sent"],
            "network_received": network["received"],
            "uptime": self.get_uptime()
        }