import time


class RecoveryPolicy:

    NO_ACTION = "NO_ACTION"
    CONTINUE_MONITORING = "CONTINUE_MONITORING"
    INCREASE_MONITORING = "INCREASE_MONITORING"
    COLLECT_EVIDENCE = "COLLECT_EVIDENCE"
    RECOMMEND_RECOVERY = "RECOMMEND_RECOVERY"
    ALLOW_RECOVERY = "ALLOW_RECOVERY"
    BLOCK_RECOVERY = "BLOCK_RECOVERY"


class RecoveryPolicyEngine(RecoveryPolicy):

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
        "explorer.exe",
    }

    def __init__(
        self,
        cooldown_seconds=60,
        persistence_required=3,
    ):
        self.cooldown_seconds = cooldown_seconds
        self.persistence_required = persistence_required

        self.last_recovery = {}
        self.anomaly_counts = {}

    # --------------------------------------------------
    # PROCESS CLASSIFICATION
    # --------------------------------------------------

    def classify_process(
        self,
        process_name,
        pid,
        controlled_test=False,
    ):
        name = (
            process_name or ""
        ).lower().strip()

        if controlled_test:
            return "CONTROLLED_TEST"

        if int(pid) in (0, 4):
            return "PROTECTED"

        if name in self.PROTECTED_NAMES:
            return "PROTECTED"

        return "NORMAL"

    # --------------------------------------------------
    # PERSISTENCE
    # --------------------------------------------------

    def update_persistence(
        self,
        pid,
        anomalous,
    ):
        pid = int(pid)

        if not anomalous:
            self.anomaly_counts.pop(pid, None)
            return 0

        current = self.anomaly_counts.get(
            pid,
            0,
        )

        current = min(
            current + 1,
            self.persistence_required,
        )

        self.anomaly_counts[pid] = current

        return current

    def get_persistence(self, pid):
        return min(
            self.anomaly_counts.get(
                int(pid),
                0,
            ),
            self.persistence_required,
        )

    def reset_process(self, pid):
        self.anomaly_counts.pop(
            int(pid),
            None,
        )

    # --------------------------------------------------
    # COOLDOWN
    # --------------------------------------------------

    def _cooldown_active(
        self,
        pid,
        current_time,
    ):
        previous = self.last_recovery.get(
            int(pid)
        )

        if previous is None:
            return False

        return (
            current_time - previous
        ) < self.cooldown_seconds

    # --------------------------------------------------
    # DECISION ENGINE
    # --------------------------------------------------

    def decide(
        self,
        result,
        confidence=0.0,
        controlled_test=False,
    ):

        pid = int(result["pid"])

        risk = float(
            result["risk"]
        )

        level = result["level"]

        status = result["status"]

        process_name = result.get(
            "process_name",
            "Unknown",
        )

        classification = self.classify_process(
            process_name,
            pid,
            controlled_test,
        )

        # --------------------------------------------------
        # PROTECTED PROCESS
        # --------------------------------------------------

        if classification == "PROTECTED":

            self.reset_process(pid)

            return {
                "action": self.BLOCK_RECOVERY,
                "classification": classification,
                "reason": (
                    "Protected/system-critical process."
                ),
                "persistence": 0,
            }

        # --------------------------------------------------
        # NORMAL PROCESS
        # --------------------------------------------------

        if status != "ANOMALY":

            self.reset_process(pid)

            return {
                "action": self.CONTINUE_MONITORING,
                "classification": classification,
                "reason": (
                    "Process is not currently anomalous."
                ),
                "persistence": 0,
            }

        # --------------------------------------------------
        # UPDATE PERSISTENCE ONCE
        # --------------------------------------------------

        persistence = self.update_persistence(
            pid,
            True,
        )

        # --------------------------------------------------
        # LOW RISK
        # --------------------------------------------------

        if risk < 20:

            return {
                "action": self.CONTINUE_MONITORING,
                "classification": classification,
                "reason": "Risk score is low.",
                "persistence": persistence,
            }

        # --------------------------------------------------
        # WAIT FOR PERSISTENCE
        # --------------------------------------------------

        if persistence < self.persistence_required:

            return {
                "action": self.COLLECT_EVIDENCE,
                "classification": classification,
                "reason": (
                    "Anomaly has not persisted long enough."
                ),
                "persistence": persistence,
            }

        # --------------------------------------------------
        # CONFIDENCE
        # --------------------------------------------------

        if confidence < 0.5:

            return {
                "action": self.INCREASE_MONITORING,
                "classification": classification,
                "reason": (
                    "Detection confidence is insufficient."
                ),
                "persistence": persistence,
            }

        # --------------------------------------------------
        # COOLDOWN
        # --------------------------------------------------

        if self._cooldown_active(
            pid,
            time.time(),
        ):

            return {
                "action": self.CONTINUE_MONITORING,
                "classification": classification,
                "reason": "Recovery cooldown is active.",
                "persistence": persistence,
            }

        # --------------------------------------------------
        # CONTROLLED TEST
        # --------------------------------------------------

        if (
            classification == "CONTROLLED_TEST"
            and risk >= 60
        ):

            return {
                "action": self.ALLOW_RECOVERY,
                "classification": classification,
                "reason": (
                    "Persistent high-risk anomaly "
                    "in controlled test process."
                ),
                "persistence": persistence,
            }

        # --------------------------------------------------
        # NORMAL PROCESS
        # --------------------------------------------------

        if risk >= 60:

            return {
                "action": self.RECOMMEND_RECOVERY,
                "classification": classification,
                "reason": (
                    "High-risk anomaly detected. "
                    "Automatic recovery is disabled "
                    "for non-controlled processes."
                ),
                "persistence": persistence,
            }

        return {
            "action": self.CONTINUE_MONITORING,
            "classification": classification,
            "reason": (
                "Risk does not justify recovery."
            ),
            "persistence": persistence,
        }

    # --------------------------------------------------
    # RECOVERY RECORD
    # --------------------------------------------------

    def mark_recovery(self, pid):

        pid = int(pid)

        self.last_recovery[pid] = time.time()

        self.reset_process(pid)