import time


class AlertEngine:

    def __init__(self):

        self.active_alerts = {}

        self.cooldown_seconds = 30

    def should_alert(self, result):

        pid = result["pid"]
        risk = result["risk"]
        status = result["status"]

        if status != "ANOMALY":
            return False

        if risk < 20:
            return False

        current_time = time.time()

        previous_alert = self.active_alerts.get(pid)

        if previous_alert is not None:

            elapsed = (
                current_time - previous_alert
            )

            if elapsed < self.cooldown_seconds:
                return False

        self.active_alerts[pid] = current_time

        return True

    def create_alert(self, result):

        features = result["features"]

        reasons = []

        if features["cpu_mean"] >= 60:

            reasons.append(
                "High sustained CPU usage"
            )

        elif features["cpu_max"] >= 90:

            reasons.append(
                "CPU usage reached a critical peak"
            )

        if features["memory_mean"] >= 1000:

            reasons.append(
                "High memory consumption"
            )

        if features["memory_slope"] >= 5:

            reasons.append(
                "Memory usage is increasing rapidly"
            )

        if features["thread_slope"] >= 5:

            reasons.append(
                "Thread count is increasing rapidly"
            )

        if result["status"] == "ANOMALY":

            reasons.append(
                "Machine-learning model detected "
                "unusual process behavior"
            )

        if not reasons:

            reasons.append(
                "Abnormal process behavior detected"
            )

        return {

            "timestamp": time.time(),

            "pid": result["pid"],

            "status": result["status"],

            "anomaly_score": result["score"],

            "risk": result["risk"],

            "level": result["level"],

            "reasons": reasons
        }

    @staticmethod
    def format_alert(alert):

        print()

        print("!" * 60)

        print("AEGIS OS SECURITY ALERT")

        print("!" * 60)

        print(
            f"PID          : {alert['pid']}"
        )

        print(
            f"AI Status    : {alert['status']}"
        )

        print(
            f"Anomaly Score: "
            f"{alert['anomaly_score']:.4f}"
        )

        print(
            f"Risk Score   : "
            f"{alert['risk']:.0f}/100"
        )

        print(
            f"Risk Level   : {alert['level']}"
        )

        print()

        print("Detected Signals:")

        for reason in alert["reasons"]:

            print(
                f"  • {reason}"
            )

        print()

        print(
            "Recommended action: CONTINUE MONITORING"
        )

        print("!" * 60)

        print()