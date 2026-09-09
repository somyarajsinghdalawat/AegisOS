class RecoveryPolicy:
    NO_ACTION = "NO_ACTION"
    CONTINUE_MONITORING = "CONTINUE_MONITORING"
    INCREASE_MONITORING = "INCREASE_MONITORING"
    COLLECT_EVIDENCE = "COLLECT_EVIDENCE"
    RECOMMEND_RECOVERY = "RECOMMEND_RECOVERY"
    ALLOW_RECOVERY = "ALLOW_RECOVERY"
    BLOCK_RECOVERY = "BLOCK_RECOVERY"


class RecoveryPolicyEngine:
    PROTECTED_NAMES = {
        "system",
        "system idle process",
        "registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "winlogon.exe",
        "svchost.exe",
        "explorer.exe"
    }

    def __init__(self, cooldown_seconds=60):
        self.cooldown_seconds = cooldown_seconds
        self.last_recovery = {}

    def classify_process(
        self,
        process_name,
        pid,
        controlled_test=False
    ):
        name = (process_name or "").lower().strip()

        if controlled_test:
            return "CONTROLLED_TEST"

        if name in self.PROTECTED_NAMES:
            return "PROTECTED"

        if pid in (0, 4):
            return "PROTECTED"

        return "NORMAL"

    def _cooldown_active(self, pid, current_time):
        previous = self.last_recovery.get(pid)

        if previous is None:
            return False

        return (current_time - previous) < self.cooldown_seconds

    def decide(
        self,
        result,
        persistent=False,
        confidence=0.0,
        controlled_test=False
    ):
        import time

        pid = result["pid"]
        risk = float(result["risk"])
        level = result["level"]
        status = result["status"]

        process_name = result.get("process_name", "Unknown")

        classification = self.classify_process(
            process_name,
            pid,
            controlled_test
        )

        if status != "ANOMALY":
            return {
                "action": self.CONTINUE_MONITORING,
                "classification": classification,
                "reason": "Process is not currently classified as anomalous."
            }

        if risk < 20:
            return {
                "action": self.CONTINUE_MONITORING,
                "classification": classification,
                "reason": "Risk score is low."
            }

        if not persistent:
            return {
                "action": self.COLLECT_EVIDENCE,
                "classification": classification,
                "reason": "Anomaly has not persisted long enough."
            }

        if confidence < 0.5:
            return {
                "action": self.INCREASE_MONITORING,
                "classification": classification,
                "reason": "Detection confidence is insufficient."
            }

        if self._cooldown_active(pid, time.time()):
            return {
                "action": self.CONTINUE_MONITORING,
                "classification": classification,
                "reason": "Recovery cooldown is active."
            }

        if classification == "PROTECTED":
            return {
                "action": self.BLOCK_RECOVERY,
                "classification": classification,
                "reason": "Protected/system-critical process."
            }

        if level == "CRITICAL" and classification == "CONTROLLED_TEST":
            return {
                "action": self.ALLOW_RECOVERY,
                "classification": classification,
                "reason": "Critical persistent anomaly in controlled test process."
            }

        if risk >= 60 and classification == "CONTROLLED_TEST":
            return {
                "action": self.ALLOW_RECOVERY,
                "classification": classification,
                "reason": "High-risk persistent anomaly in controlled test process."
            }

        if risk >= 60:
            return {
                "action": self.RECOMMEND_RECOVERY,
                "classification": classification,
                "reason": "High-risk anomaly detected but process is not a controlled test."
            }

        return {
            "action": self.CONTINUE_MONITORING,
            "classification": classification,
            "reason": "Risk does not justify recovery."
        }

    def mark_recovery(self, pid):
        import time

        self.last_recovery[pid] = time.time()