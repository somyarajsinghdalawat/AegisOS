import os
import signal
import time


class SafeRecoveryEngine:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.controlled_pids = set()

    def register_controlled_process(self, pid):
        self.controlled_pids.add(int(pid))

    def unregister_controlled_process(self, pid):
        self.controlled_pids.discard(int(pid))

    def is_controlled_process(self, pid):
        return int(pid) in self.controlled_pids

    def _is_alive(self, pid):
        try:
            os.kill(int(pid), 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False

    def terminate_controlled_process(self, pid, reason=""):
        pid = int(pid)

        if not self.is_controlled_process(pid):
            return {
                "success": False,
                "status": "BLOCKED",
                "action": "TERMINATE",
                "message": "PID is not registered as a controlled test process."
            }

        if not self._is_alive(pid):
            return {
                "success": False,
                "status": "ALREADY_STOPPED",
                "action": "TERMINATE",
                "message": "Process is already stopped."
            }

        if self.dry_run:
            print()
            print("DRY RUN:")
            print(f"Would terminate PID {pid}")
            print(f"Reason: {reason}")
            print("Process classified as safe-to-recover")
            print()

            return {
                "success": True,
                "status": "DRY_RUN",
                "action": "TERMINATE",
                "message": "Termination simulated."
            }

        try:
            os.kill(pid, signal.SIGTERM)

            time.sleep(1)

            if self._is_alive(pid):
                return {
                    "success": False,
                    "status": "FAILED",
                    "action": "TERMINATE",
                    "message": "Process is still running after termination request."
                }

            return {
                "success": True,
                "status": "SUCCESS",
                "action": "TERMINATE",
                "message": "Controlled test process terminated."
            }

        except PermissionError:
            return {
                "success": False,
                "status": "FAILED",
                "action": "TERMINATE",
                "message": "Permission denied."
            }

        except ProcessLookupError:
            return {
                "success": True,
                "status": "SUCCESS",
                "action": "TERMINATE",
                "message": "Process stopped before termination completed."
            }

        except OSError as error:
            return {
                "success": False,
                "status": "FAILED",
                "action": "TERMINATE",
                "message": str(error)
            }

    def execute(self, policy_result, pid, reason=""):
        action = policy_result["action"]

        if action == "ALLOW_RECOVERY":
            return self.terminate_controlled_process(
                pid,
                reason=reason
            )

        if action == "RECOMMEND_RECOVERY":
            return {
                "success": False,
                "status": "RECOMMENDED",
                "action": "NONE",
                "message": "Recovery recommended but not automatically executed."
            }

        if action == "BLOCK_RECOVERY":
            return {
                "success": False,
                "status": "BLOCKED",
                "action": "NONE",
                "message": "Recovery blocked by safety policy."
            }

        if action == "INCREASE_MONITORING":
            return {
                "success": True,
                "status": "MONITORING",
                "action": "MONITOR",
                "message": "Monitoring frequency should be increased."
            }

        if action == "COLLECT_EVIDENCE":
            return {
                "success": True,
                "status": "EVIDENCE_COLLECTION",
                "action": "COLLECT_EVIDENCE",
                "message": "Additional evidence should be collected."
            }

        return {
            "success": True,
            "status": "MONITORING",
            "action": "MONITOR",
            "message": "Continue monitoring."
        }