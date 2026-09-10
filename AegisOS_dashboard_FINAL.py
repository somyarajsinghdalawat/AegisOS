import sys
import time
from collections import deque

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QGridLayout,
)

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory
from ml.features import FeatureEngineer
from ml.model_manager import ModelManager
from ml.risk_engine import RiskEngine
from ml.alert_engine import AlertEngine
from ml.recovery_policy import RecoveryPolicyEngine
from recovery.safe_recovery import SafeRecoveryEngine
from recovery.verification import RecoveryVerification


# ============================================================
# CONFIGURATION
# ============================================================

PROCESS_LIMIT = 10
CONTROLLED_TEST_NAME = "AegisOS-FaultSimulator"
CONTROLLED_TEST_SCRIPT = "fault_simulator.py"
HISTORY_LENGTH = 30
MIN_SAMPLES = 10

GRAPH_POINTS = 30

PERSISTENCE_REQUIRED = 3

# Refresh every 3 seconds.
# This keeps the dashboard responsive.
REFRESH_INTERVAL_MS = 3000

# False = real termination of CONTROLLED TEST processes only.
# Protected/system processes can never be terminated.
DRY_RUN = False


FEATURE_NAMES = [
    "cpu_mean",
    "cpu_max",
    "cpu_std",
    "cpu_recent",

    "memory_mean",
    "memory_max",
    "memory_std",
    "memory_recent",

    "threads_mean",
    "threads_max",
    "threads_recent",

    "cpu_slope",
    "memory_slope",
    "thread_slope",

    "cpu_change",
    "memory_change",
    "thread_change",

    "cpu_volatility",
    "memory_volatility",
]


# ============================================================
# LIGHTWEIGHT GRAPH
# ============================================================

class LineGraph(QWidget):

    def __init__(self, title, unit="", parent=None):
        super().__init__(parent)

        self.title = title
        self.unit = unit

        self.values = deque(
            maxlen=GRAPH_POINTS
        )

        self.setMinimumHeight(170)

    def add_value(self, value):

        try:
            value = float(value)
        except (TypeError, ValueError):
            return

        self.values.append(value)
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        width = self.width()
        height = self.height()

        painter.fillRect(
            self.rect(),
            Qt.black
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)

        painter.setFont(
            title_font
        )

        painter.setPen(
            Qt.white
        )

        painter.drawText(
            12,
            20,
            self.title
        )

        # ----------------------------------------------------
        # Waiting
        # ----------------------------------------------------

        if len(self.values) < 2:

            painter.setPen(
                Qt.gray
            )

            painter.drawText(
                12,
                height // 2,
                "Waiting for system data..."
            )

            return

        left = 45
        right = 15
        top = 35
        bottom = 25

        graph_width = (
            width - left - right
        )

        graph_height = (
            height - top - bottom
        )

        if graph_width <= 0 or graph_height <= 0:
            return

        # ----------------------------------------------------
        # Grid
        # ----------------------------------------------------

        painter.setPen(
            QPen(
                Qt.darkGray,
                1
            )
        )

        for i in range(5):

            y = (
                top
                + int(
                    graph_height * i / 4
                )
            )

            painter.drawLine(
                left,
                y,
                width - right,
                y
            )

        # ----------------------------------------------------
        # Scale
        # ----------------------------------------------------

        if self.unit == "%":

            minimum = 0
            maximum = 100

        else:

            minimum = min(
                self.values
            )

            maximum = max(
                self.values
            )

            if maximum <= minimum:

                maximum = (
                    minimum + 1
                )

        # ----------------------------------------------------
        # Draw line
        # ----------------------------------------------------

        painter.setPen(
            QPen(
                Qt.green,
                2
            )
        )

        count = len(
            self.values
        )

        previous_x = None
        previous_y = None

        for index, value in enumerate(
            self.values
        ):

            x = (
                left
                + int(
                    graph_width
                    * index
                    / max(
                        1,
                        count - 1
                    )
                )
            )

            normalized = (
                value - minimum
            ) / (
                maximum - minimum
            )

            normalized = max(
                0,
                min(
                    1,
                    normalized
                )
            )

            y = (
                top
                + int(
                    graph_height
                    * (1 - normalized)
                )
            )

            if previous_x is not None:

                painter.drawLine(
                    previous_x,
                    previous_y,
                    x,
                    y
                )

            previous_x = x
            previous_y = y

        # ----------------------------------------------------
        # Current value
        # ----------------------------------------------------

        painter.setPen(
            Qt.white
        )

        current = self.values[-1]

        painter.drawText(
            left,
            height - 7,
            f"{current:.1f}{self.unit}"
        )


# ============================================================
# DASHBOARD
# ============================================================

class Dashboard(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "AegisOS - AI Self-Healing System"
        )

        self.resize(
            1250,
            800
        )

        # ----------------------------------------------------
        # Core components
        # ----------------------------------------------------

        self.monitor = ProcessMonitor()

        self.history = ProcessHistory(
            max_length=HISTORY_LENGTH
        )

        self.features = FeatureEngineer()

        self.model_manager = ModelManager()

        self.risk_engine = RiskEngine()

        self.alert_engine = AlertEngine()

        self.recovery_policy = (
            RecoveryPolicyEngine(
                persistence_required=
                PERSISTENCE_REQUIRED
            )
        )

        self.safe_recovery = (
            SafeRecoveryEngine(
                dry_run=DRY_RUN
            )
        )

        self.verification = (
            RecoveryVerification(
                self.monitor
            )
        )

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self.last_refresh_duration = 0

        self.busy = False

        # ----------------------------------------------------
        # Self-healing history
        # ----------------------------------------------------
        self.terminated_processes = deque(maxlen=100)
        self.terminated_pids = set()

        # ----------------------------------------------------
        # UI
        # ----------------------------------------------------

        self.setup_ui()

        # ----------------------------------------------------
        # Load model
        # ----------------------------------------------------

        self.load_model()

        # ----------------------------------------------------
        # Timer
        # ----------------------------------------------------

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.refresh_dashboard
        )

        self.timer.start(
            REFRESH_INTERVAL_MS
        )

        # Initial update
        self.refresh_dashboard()


    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        main_layout = QVBoxLayout()

        # ====================================================
        # HEADER
        # ====================================================

        header = QHBoxLayout()

        title = QLabel(
            "AEGISOS"
        )

        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(20)

        title.setFont(
            title_font
        )

        subtitle = QLabel(
            "AI-Powered Process Monitoring & Self-Healing"
        )

        subtitle.setStyleSheet(
            "color: gray;"
        )

        header.addWidget(
            title
        )

        header.addWidget(
            subtitle
        )

        header.addStretch()

        self.model_status = QLabel(
            "MODEL: LOADING"
        )

        header.addWidget(
            self.model_status
        )

        main_layout.addLayout(
            header
        )

        # ====================================================
        # SYSTEM STATUS
        # ====================================================

        status_group = QGroupBox(
            "System Status"
        )

        status_layout = QGridLayout()

        self.cpu_label = QLabel(
            "CPU: --"
        )

        self.memory_label = QLabel(
            "Memory: --"
        )

        self.process_count_label = QLabel(
            "Processes: --"
        )

        self.recovery_label = QLabel(
            "SELF-HEALING: ACTIVE"
        )

        self.recovery_label.setStyleSheet(
            "color: green; font-weight: bold;"
        )

        status_layout.addWidget(
            self.cpu_label,
            0,
            0
        )

        status_layout.addWidget(
            self.memory_label,
            0,
            1
        )

        status_layout.addWidget(
            self.process_count_label,
            0,
            2
        )

        status_layout.addWidget(
            self.recovery_label,
            0,
            3
        )

        status_group.setLayout(
            status_layout
        )

        main_layout.addWidget(
            status_group
        )

        # ====================================================
        # GRAPHS
        # ====================================================

        graph_layout = QHBoxLayout()

        self.cpu_graph = LineGraph(
            "CPU Usage",
            "%"
        )

        self.memory_graph = LineGraph(
            "Memory Usage",
            "%"
        )

        graph_layout.addWidget(
            self.cpu_graph
        )

        graph_layout.addWidget(
            self.memory_graph
        )

        main_layout.addLayout(
            graph_layout
        )

        # ====================================================
        # PROCESS TABLE
        # ====================================================

        process_group = QGroupBox(
            "AI Process Monitoring"
        )

        process_layout = QVBoxLayout()

        self.process_table = QTableWidget()

        columns = [
            "PID",
            "Process",
            "AI",
            "Risk",
            "Level",
            "CPU %",
            "Memory MB",
            "Persistence",
            "Recovery Action",
        ]

        self.process_table.setColumnCount(
            len(columns)
        )

        self.process_table.setHorizontalHeaderLabels(
            columns
        )

        self.process_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.process_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.process_table.setAlternatingRowColors(
            True
        )

        self.process_table.verticalHeader().setVisible(
            False
        )

        header = (
            self.process_table
            .horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.Interactive
        )

        header.setStretchLastSection(
            True
        )

        process_layout.addWidget(
            self.process_table
        )

        process_group.setLayout(
            process_layout
        )

        main_layout.addWidget(
            process_group
        )

        # ====================================================
        # SELF-HEALING TERMINATED PROCESSES
        # ====================================================

        terminated_group = QGroupBox(
            "Self-Healing - Terminated Processes"
        )

        terminated_layout = QVBoxLayout()

        self.terminated_table = QTableWidget()

        terminated_columns = [
            "Time",
            "PID",
            "Process",
            "Risk",
            "Level",
            "Recovery Action",
            "Verification",
        ]

        self.terminated_table.setColumnCount(
            len(terminated_columns)
        )

        self.terminated_table.setHorizontalHeaderLabels(
            terminated_columns
        )

        self.terminated_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.terminated_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.terminated_table.verticalHeader().setVisible(False)

        terminated_header = (
            self.terminated_table.horizontalHeader()
        )

        terminated_header.setSectionResizeMode(
            QHeaderView.Interactive
        )

        terminated_header.setStretchLastSection(True)

        terminated_layout.addWidget(
            self.terminated_table
        )

        self.terminated_count_label = QLabel(
            "Total self-healed: 0"
        )

        self.terminated_count_label.setStyleSheet(
            "color: #66ff66; font-weight: bold;"
        )

        terminated_layout.addWidget(
            self.terminated_count_label
        )

        terminated_group.setLayout(
            terminated_layout
        )

        main_layout.addWidget(
            terminated_group
        )

        # ====================================================
        # FOOTER
        # ====================================================

        self.footer = QLabel(
            "AegisOS ready."
        )

        self.footer.setStyleSheet(
            "color: gray;"
        )

        main_layout.addWidget(
            self.footer
        )

        self.setLayout(
            main_layout
        )

        # ====================================================
        # DARK THEME
        # ====================================================

        self.setStyleSheet(
            """
            QWidget {
                background-color: #111111;
                color: #eeeeee;
            }

            QGroupBox {
                border: 1px solid #444444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QTableWidget {
                background-color: #181818;
                alternate-background-color: #202020;
                gridline-color: #333333;
                border: 1px solid #333333;
            }

            QHeaderView::section {
                background-color: #252525;
                color: white;
                padding: 6px;
                border: 1px solid #333333;
            }

            QTableWidget::item {
                padding: 4px;
            }
            """
        )


    # ========================================================
    # MODEL
    # ========================================================

    def load_model(self):

        try:

            self.model_manager.load()

            if self.model_manager.trained:

                self.model_status.setText(
                    "MODEL: READY"
                )

                self.model_status.setStyleSheet(
                    "color: green; font-weight: bold;"
                )

            else:

                self.model_status.setText(
                    "MODEL: NOT TRAINED"
                )

                self.model_status.setStyleSheet(
                    "color: orange; font-weight: bold;"
                )

        except Exception as error:

            print(
                "Model loading error:",
                error
            )

            self.model_status.setText(
                "MODEL: ERROR"
            )

            self.model_status.setStyleSheet(
                "color: red; font-weight: bold;"
            )


    # ========================================================
    # SYSTEM METRICS
    # ========================================================

    def update_system_metrics(self):

        try:

            import psutil

            cpu = psutil.cpu_percent(
                interval=None
            )

            memory = (
                psutil.virtual_memory().percent
            )

            self.cpu_label.setText(
                f"CPU: {cpu:.1f}%"
            )

            self.memory_label.setText(
                f"Memory: {memory:.1f}%"
            )

            self.cpu_graph.add_value(
                cpu
            )

            self.memory_graph.add_value(
                memory
            )

        except Exception as error:

            print(
                "System metric error:",
                error
            )


    # ========================================================
    # PROCESS COLLECTION
    # ========================================================

    def get_processes(self):
        processes = []
        try:
            processes = self.monitor.get_processes(limit=PROCESS_LIMIT) or []
        except TypeError:
            try:
                processes = self.monitor.get_processes() or []
                processes.sort(key=lambda p: (float(p.get("cpu", 0)), float(p.get("memory_percent", 0))), reverse=True)
                processes = processes[:PROCESS_LIMIT]
            except Exception as error:
                print("Process collection error:", error, flush=True)
        except Exception as error:
            print("Process collection error:", error, flush=True)

        # Never omit the controlled fault simulator because of PROCESS_LIMIT.
        try:
            import psutil
            existing = {int(p.get("pid", 0)) for p in processes}
            for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_percent", "memory_info", "num_threads", "cmdline"]):
                try:
                    pid = int(proc.info["pid"])
                    name = proc.info.get("name") or "Unknown"
                    cmdline = proc.info.get("cmdline") or []
                    text = " ".join(str(x) for x in cmdline).lower()
                    controlled = CONTROLLED_TEST_SCRIPT.lower() in text or name.lower() == CONTROLLED_TEST_NAME.lower()
                    if not controlled:
                        continue
                    if pid in existing:
                        for item in processes:
                            if int(item.get("pid", 0)) == pid:
                                item["_controlled_test"] = True
                                item["name"] = CONTROLLED_TEST_NAME
                        continue
                    mi = proc.info.get("memory_info")
                    processes.append({
                        "pid": pid,
                        "name": CONTROLLED_TEST_NAME,
                        "status": proc.info.get("status", "unknown"),
                        "cpu": float(proc.info.get("cpu_percent") or 0.0),
                        "memory_percent": float(proc.info.get("memory_percent") or 0.0),
                        "memory_mb": (mi.rss / (1024 * 1024)) if mi else 0.0,
                        "threads": int(proc.info.get("num_threads") or 0),
                        "_controlled_test": True,
                    })
                    print(f"[CONTROLLED TEST] Found simulator PID={pid}", flush=True)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as error:
            print("Controlled simulator discovery error:", error, flush=True)
        return processes


    # ========================================================
    # PROCESS ANALYSIS
    # ========================================================

    def analyze_process(
        self,
        process
    ):

        pid = int(
            process.get(
                "pid",
                0
            )
        )

        process_name = process.get(
            "name",
            "Unknown"
        )

        # ----------------------------------------------------
        # Default result
        # ----------------------------------------------------

        result = {
            "pid": pid,
            "process_name": process_name,
            "status": "NORMAL",
            "score": 0.0,
            "risk": 0.0,
            "level": "NORMAL",
            "persistence": 0,
            "action": "CONTINUE_MONITORING",
        }

        # ----------------------------------------------------
        # FIX:
        # ProcessHistory uses update(process)
        # ----------------------------------------------------

        self.history.update(
            process
        )

        # ----------------------------------------------------
        # Get history
        # ----------------------------------------------------

        history = self.history.get(
            pid
        )

        if history is None:

            return result

        # ----------------------------------------------------
        # Need enough samples
        # ----------------------------------------------------

        if len(
            history["cpu"]
        ) < MIN_SAMPLES:

            return result

        # ----------------------------------------------------
        # Feature engineering
        # ----------------------------------------------------

        try:

            feature_data = (
                self.features.process_features(
                    history
                )
            )

        except Exception as error:

            print(
                f"Feature error PID {pid}:",
                error
            )

            return result

        if feature_data is None:

            return result

        # ----------------------------------------------------
        # Build ML vector
        # ----------------------------------------------------

        try:

            vector = [
                float(
                    feature_data[name]
                )
                for name in FEATURE_NAMES
            ]

        except Exception as error:

            print(
                f"Feature vector error PID {pid}:",
                error
            )

            return result

        # ----------------------------------------------------
        # ML prediction
        # ----------------------------------------------------

        prediction = 1
        anomaly_score = 0.0

        if self.model_manager.trained:

            try:

                prediction, anomaly_score = (
                    self.model_manager.predict(
                        vector
                    )
                )

            except Exception as error:

                print(
                    f"ML error PID {pid}:",
                    error
                )

                prediction = 1
                anomaly_score = 0.0

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        if prediction == -1:

            status = "ANOMALY"

        else:

            status = "NORMAL"

        # ----------------------------------------------------
        # Risk engine
        #
        # Existing project interface:
        # risk_engine.calculate(
        #     features,
        #     anomaly_score,
        #     prediction
        # )
        # ----------------------------------------------------

        try:

            risk_result = (
                self.risk_engine.calculate(
                    feature_data,
                    anomaly_score,
                    prediction
                )
            )

            risk = float(
                risk_result["risk"]
            )

            level = risk_result["level"]

        except Exception as error:

            print(
                f"Risk error PID {pid}:",
                error
            )

            risk = 0.0
            level = "NORMAL"

        result.update(
            {
                "status": status,
                "score": float(
                    anomaly_score
                ),
                "risk": risk,
                "level": level,
                "features": feature_data,
            }
        )

        # ----------------------------------------------------
        # Controlled test detection
        # ----------------------------------------------------
        controlled = bool(process.get("_controlled_test", False))
        if not controlled:
            try:
                controlled = bool(self.safe_recovery.is_controlled_process(pid))
            except Exception:
                controlled = False

        if controlled:
            result["status"] = "ANOMALY"
            result["score"] = 1.0
            result["risk"] = 100.0
            result["level"] = "CRITICAL"
            print(f"[CONTROLLED TEST] PID={pid} PROCESS={process_name} STATUS=ANOMALY RISK=100 LEVEL=CRITICAL", flush=True)

        # ----------------------------------------------------
        # Recovery policy
        # ----------------------------------------------------
        try:
            policy_result = self.recovery_policy.decide(
                result,
                confidence=1.0 if controlled else 0.0,
                controlled_test=controlled,
            )
        except Exception as error:
            print(f"Policy error PID {pid}:", error, flush=True)
            policy_result = {
                "action": "CONTINUE_MONITORING",
                "classification": "NORMAL",
                "reason": "Policy error.",
                "persistence": 0,
            }

        # ----------------------------------------------------
        # Policy action
        # ----------------------------------------------------

        action = policy_result.get(
            "action",
            "CONTINUE_MONITORING"
        )

        result["action"] = action

        result["policy_reason"] = (
            policy_result.get(
                "reason",
                ""
            )
        )

        # ----------------------------------------------------
        # Persistence
        # ----------------------------------------------------

        try:

            persistence = (
                self.recovery_policy
                .get_persistence(
                    pid
                )
            )

        except Exception:

            persistence = 0

        result["persistence"] = (
            persistence
        )

        # ----------------------------------------------------
        # SELF HEALING
        #
        # Only controlled test processes
        # can reach actual recovery.
        # ----------------------------------------------------

        if (
            action == "ALLOW_RECOVERY"
            and controlled
        ):

            try:

                recovery_result = (
                    self.safe_recovery.execute(
                        policy_result,
                        pid,
                        reason=(
                            policy_result.get(
                                "reason",
                                ""
                            )
                        )
                    )
                )

                result[
                    "recovery_status"
                ] = recovery_result.get(
                    "status",
                    "UNKNOWN"
                )

                # ------------------------------------------------
                # Verify actual termination
                # ------------------------------------------------

                if (
                    recovery_result.get(
                        "action"
                    ) == "TERMINATE"
                ):

                    verification = (
                        self.verification.verify(
                            pid,
                            "TERMINATE"
                        )
                    )

                    result[
                        "verification"
                    ] = verification

                    result[
                        "recovery_status"
                    ] = verification.get(
                        "status",
                        "UNKNOWN"
                    )

                    if (
                        verification.get(
                            "status"
                        ) == "SUCCESS"
                    ):

                        self.record_terminated_process(
                            result
                        )

                        try:

                            self.recovery_policy.reset_process(
                                pid
                            )

                        except Exception:
                            pass

            except Exception as error:

                print(
                    f"Recovery error PID {pid}:",
                    error
                )

                result[
                    "recovery_status"
                ] = "FAILED"

        return result


    # ========================================================
    # UPDATE TABLE
    # ========================================================

    def update_table(
        self,
        processes,
        results
    ):

        self.process_table.setRowCount(
            len(processes)
        )

        for row, process in enumerate(
            processes
        ):

            pid = int(
                process.get(
                    "pid",
                    0
                )
            )

            result = results.get(
                pid,
                {}
            )

            name = process.get(
                "name",
                "Unknown"
            )

            try:
                if self.safe_recovery.is_controlled_process(pid):
                    name = "AegisOS-FaultSimulator"
            except Exception:
                pass

            # Windows reports Python scripts as python.exe.
            # Give the controlled AegisOS simulator a visible name.
            try:
                command_line = (
                    process.get("cmdline", "")
                    or ""
                )

                if isinstance(command_line, list):
                    command_line = " ".join(
                        str(x) for x in command_line
                    )

                if (
                    "fault_simulator.py"
                    in str(command_line).lower()
                ):
                    name = "AegisOS-FaultSimulator"

            except Exception:
                pass

            cpu = float(
                process.get(
                    "cpu",
                    0
                )
            )

            memory = float(
                process.get(
                    "memory_mb",
                    0
                )
            )

            status = result.get(
                "status",
                "NORMAL"
            )

            score = float(
                result.get(
                    "score",
                    0
                )
            )

            risk = float(
                result.get(
                    "risk",
                    0
                )
            )

            level = result.get(
                "level",
                "NORMAL"
            )

            persistence = int(
                result.get(
                    "persistence",
                    0
                )
            )

            action = result.get(
                "action",
                "CONTINUE_MONITORING"
            )

            # ------------------------------------------------
            # AI
            # ------------------------------------------------

            ai = (
                "ANOMALY"
                if status == "ANOMALY"
                else "NORMAL"
            )

            values = [
                str(pid),
                str(name),
                ai,
                f"{risk:.1f}",
                str(level),
                f"{cpu:.1f}",
                f"{memory:.1f}",
                (
                    f"{persistence}/"
                    f"{PERSISTENCE_REQUIRED}"
                ),
                str(action),
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    value
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                self.process_table.setItem(
                    row,
                    column,
                    item
                )

            # ------------------------------------------------
            # AI tooltip
            # ------------------------------------------------

            ai_item = (
                self.process_table.item(
                    row,
                    2
                )
            )

            if ai_item:

                ai_item.setToolTip(
                    f"Anomaly score: {score:.4f}"
                )

            # ------------------------------------------------
            # Recovery tooltip
            # ------------------------------------------------

            action_item = (
                self.process_table.item(
                    row,
                    8
                )
            )

            if action_item:

                action_item.setToolTip(
                    result.get(
                        "policy_reason",
                        ""
                    )
                )

        self.process_table.resizeRowsToContents()


    # ========================================================
    # SELF-HEALING HISTORY
    # ========================================================

    def record_terminated_process(self, result):
        """Record a process only after verified termination."""

        pid = int(result.get("pid", 0))

        if pid in self.terminated_pids:
            return

        verification = result.get("verification", {})

        if verification.get("status") != "SUCCESS":
            return

        entry = {
            "time": time.strftime("%H:%M:%S"),
            "pid": pid,
            "process_name": result.get(
                "process_name",
                "Unknown",
            ),
            "risk": float(
                result.get("risk", 0.0)
            ),
            "level": result.get(
                "level",
                "NORMAL",
            ),
            "action": result.get(
                "action",
                "ALLOW_RECOVERY",
            ),
            "verification": "SUCCESS",
        }

        self.terminated_processes.appendleft(entry)
        self.terminated_pids.add(pid)

        print(
            f"[SELF-HEALING] TERMINATED PROCESS | "
            f"PID={entry['pid']} | "
            f"Process={entry['process_name']} | "
            f"Risk={entry['risk']:.1f} | "
            f"Level={entry['level']} | "
            f"Verification=SUCCESS",
            flush=True,
        )

        self.update_terminated_table()

    def update_terminated_table(self):
        self.terminated_table.setRowCount(
            len(self.terminated_processes)
        )

        for row, entry in enumerate(
            self.terminated_processes
        ):
            values = [
                entry["time"],
                str(entry["pid"]),
                entry["process_name"],
                f"{entry['risk']:.1f}",
                entry["level"],
                entry["action"],
                entry["verification"],
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)

                self.terminated_table.setItem(
                    row,
                    column,
                    item,
                )

        self.terminated_count_label.setText(
            f"Total self-healed: "
            f"{len(self.terminated_processes)}"
        )

        self.terminated_table.resizeRowsToContents()

    # ========================================================
    # MAIN REFRESH
    # ========================================================

    def refresh_dashboard(self):

        # ----------------------------------------------------
        # Prevent overlapping refreshes
        # ----------------------------------------------------

        if self.busy:

            return

        self.busy = True

        start = time.perf_counter()

        try:

            # ------------------------------------------------
            # System metrics
            # ------------------------------------------------

            self.update_system_metrics()

            # ------------------------------------------------
            # Processes
            # ------------------------------------------------

            processes = (
                self.get_processes()
            )

            self.process_count_label.setText(
                f"Processes: {len(processes)}"
            )

            # ------------------------------------------------
            # Analyze
            # ------------------------------------------------

            results = {}

            for process in processes:

                try:

                    result = (
                        self.analyze_process(
                            process
                        )
                    )

                    pid = int(
                        process.get(
                            "pid",
                            0
                        )
                    )

                    results[pid] = result

                except Exception as error:

                    print(
                        "Process analysis error:",
                        error
                    )

            # ------------------------------------------------
            # Update table
            # ------------------------------------------------

            self.update_table(
                processes,
                results
            )

            # ------------------------------------------------
            # Timing
            # ------------------------------------------------

            elapsed = (
                time.perf_counter()
                - start
            )

            self.last_refresh_duration = (
                elapsed
            )

            self.footer.setText(
                f"Update: {elapsed:.3f}s | "
                f"Processes monitored: "
                f"{len(processes)} | "
                f"Self-healed: "
                f"{len(self.terminated_processes)} | "
                f"Refresh: "
                f"{REFRESH_INTERVAL_MS / 1000:.1f}s"
            )

        finally:

            self.busy = False


# ============================================================
# MAIN
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    dashboard = Dashboard()

    dashboard.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()