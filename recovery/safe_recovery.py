import time

import psutil


class SafeRecoveryEngine:

    CONTROLLED_MARKERS = {
        "fault_simulator.py",
        "test_fault.py",
        "controlled_fault.py",
    }

    PROTECTED_PIDS = {
        0,
        4,
    }

    def __init__(
        self,
        dry_run=False,
    ):
        self.dry_run = dry_run
        self.controlled_pids = set()

    # --------------------------------------------------
    # CONTROLLED PROCESS REGISTRATION
    # --------------------------------------------------

    def register_controlled_process(
        self,
        pid,
    ):
        self.controlled_pids.add(
            int(pid)
        )

    def unregister_controlled_process(
        self,
        pid,
    ):
        self.controlled_pids.discard(
            int(pid)
        )

    def is_controlled_process(
        self,
        pid,
    ):
        pid = int(pid)

        if pid in self.controlled_pids:
            return True

        try:
            process = psutil.Process(pid)

            command_line = " ".join(
                process.cmdline()
            ).lower()

            for marker in self.CONTROLLED_MARKERS:

                if marker.lower() in command_line:
                    return True

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            pass

        return False

    # --------------------------------------------------
    # SAFETY
    # --------------------------------------------------

    def _is_protected_pid(
        self,
        pid,
    ):
        return int(pid) in self.PROTECTED_PIDS

    # --------------------------------------------------
    # PROCESS STATE
    # --------------------------------------------------

    def _is_alive(
        self,
        pid,
    ):
        try:
            process = psutil.Process(
                int(pid)
            )

            return process.is_running()

        except (
            psutil.NoSuchProcess,
            psutil.ZombieProcess,
        ):
            return False

        except psutil.AccessDenied:
            return True

    # --------------------------------------------------
    # TERMINATION
    # --------------------------------------------------

    def terminate_controlled_process(
        self,
        pid,
        reason="",
    ):

        pid = int(pid)

        # NEVER terminate protected PIDs
        if self._is_protected_pid(pid):

            return {
                "success": False,
                "status": "BLOCKED",
                "action": "TERMINATE",
                "message": (
                    "Protected PID."
                ),
            }

        # MUST be controlled
        if not self.is_controlled_process(pid):

            return {
                "success": False,
                "status": "BLOCKED",
                "action": "TERMINATE",
                "message": (
                    "PID is not a controlled "
                    "test process."
                ),
            }

        if not self._is_alive(pid):

            return {
                "success": True,
                "status": "ALREADY_STOPPED",
                "action": "TERMINATE",
                "message": (
                    "Process is already stopped."
                ),
            }

        if self.dry_run:

            print(
                f"[SAFE RECOVERY] DRY RUN PID={pid}"
            )

            return {
                "success": True,
                "status": "DRY_RUN",
                "action": "TERMINATE",
                "message": (
                    "Termination simulated."
                ),
            }

        try:

            process = psutil.Process(pid)

            process.terminate()

            try:
                process.wait(
                    timeout=5
                )

            except psutil.TimeoutExpired:

                process.kill()

                process.wait(
                    timeout=3
                )

            if self._is_alive(pid):

                return {
                    "success": False,
                    "status": "FAILED",
                    "action": "TERMINATE",
                    "message": (
                        "Process is still running "
                        "after recovery."
                    ),
                }

            return {
                "success": True,
                "status": "SUCCESS",
                "action": "TERMINATE",
                "message": (
                    "Controlled test process terminated."
                ),
            }

        except psutil.NoSuchProcess:

            return {
                "success": True,
                "status": "ALREADY_STOPPED",
                "action": "TERMINATE",
                "message": (
                    "Process stopped during recovery."
                ),
            }

        except psutil.AccessDenied:

            return {
                "success": False,
                "status": "PERMISSION_DENIED",
                "action": "TERMINATE",
                "message": (
                    "Permission denied."
                ),
            }

        except Exception as error:

            return {
                "success": False,
                "status": "FAILED",
                "action": "TERMINATE",
                "message": str(error),
            }

    # --------------------------------------------------
    # POLICY EXECUTION
    # --------------------------------------------------

    def execute(
        self,
        policy_result,
        pid,
        reason="",
    ):

        action = policy_result["action"]

        if action == "ALLOW_RECOVERY":

            return self.terminate_controlled_process(
                pid,
                reason=reason,
            )

        if action == "RECOMMEND_RECOVERY":

            return {
                "success": False,
                "status": "RECOMMENDED",
                "action": "NONE",
                "message": (
                    "Recovery recommended but "
                    "not automatically executed."
                ),
            }

        if action == "BLOCK_RECOVERY":

            return {
                "success": False,
                "status": "BLOCKED",
                "action": "NONE",
                "message": (
                    "Recovery blocked by safety policy."
                ),
            }

        if action == "INCREASE_MONITORING":

            return {
                "success": True,
                "status": "MONITORING",
                "action": "MONITOR",
                "message": (
                    "Monitoring frequency should increase."
                ),
            }

        if action == "COLLECT_EVIDENCE":

            return {
                "success": True,
                "status": "EVIDENCE_COLLECTION",
                "action": "COLLECT_EVIDENCE",
                "message": (
                    "Additional evidence required."
                ),
            }

        return {
            "success": True,
            "status": "MONITORING",
            "action": "MONITOR",
            "message": (
                "Continue monitoring."
            ),
        }