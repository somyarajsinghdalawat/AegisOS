import sys
import time
import sqlite3
from pathlib import Path
from collections import deque

import psutil
import pyqtgraph as pg

from PySide6.QtCore import Qt, QTimer, QObject, Signal, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFrame,
    QPushButton,
    QTabWidget,
    QAbstractItemView,
    QMessageBox,
)

from collector.process_monitor import ProcessMonitor
from detection.process_history import ProcessHistory
from ml.features import FeatureEngineer
from ml.model_manager import ModelManager
from ml.risk_engine import RiskEngine
from ml.alert_engine import AlertEngine


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "aegisos.db"

PROCESS_LIMIT = 25
HISTORY_LENGTH = 30
MIN_SAMPLES = 10
UPDATE_INTERVAL = 1000

MAX_CPU_POINTS = 60
MAX_MEMORY_POINTS = 60


# ============================================================
# COLORS / STYLE
# ============================================================

STYLE = """
QMainWindow {
    background-color: #0b1220;
}

QWidget {
    color: #e5e7eb;
    font-family: Segoe UI;
}

QFrame#card {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 10px;
}

QLabel#title {
    font-size: 26px;
    font-weight: bold;
}

QLabel#subtitle {
    color: #9ca3af;
    font-size: 13px;
}

QLabel#metric_title {
    color: #9ca3af;
    font-size: 12px;
}

QLabel#metric_value {
    font-size: 25px;
    font-weight: bold;
}

QTableWidget {
    background-color: #111827;
    border: 1px solid #1f2937;
    gridline-color: #1f2937;
    selection-background-color: #243244;
    alternate-background-color: #0f172a;
}

QHeaderView::section {
    background-color: #172033;
    color: #d1d5db;
    border: none;
    padding: 8px;
    font-weight: bold;
}

QPushButton {
    background-color: #1f2937;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 8px 14px;
}

QPushButton:hover {
    background-color: #374151;
}

QTabWidget::pane {
    border: 1px solid #1f2937;
    background-color: #0b1220;
}

QTabBar::tab {
    background-color: #111827;
    padding: 10px 18px;
    border: 1px solid #1f2937;
}

QTabBar::tab:selected {
    background-color: #1f2937;
}

QLabel#status {
    color: #86efac;
    font-weight: bold;
}
"""


# ============================================================
# MONITOR WORKER
# ============================================================

class MonitorWorker(QObject):

    data_ready = Signal(object)
    error = Signal(str)

    def __init__(self):
        super().__init__()

        self.monitor = ProcessMonitor()
        self.history = ProcessHistory(
            max_length=HISTORY_LENGTH
        )

        self.feature_engineer = FeatureEngineer()
        self.risk_engine = RiskEngine()
        self.model_manager = ModelManager()
        self.alert_engine = AlertEngine()

        self.running = True
        self.trained = False

    def train_model(self):

        try:

            training_histories = {}

            for _ in range(30):

                processes = self.monitor.get_processes(
                    limit=PROCESS_LIMIT
                )

                for process in processes:

                    pid = process["pid"]

                    if pid not in training_histories:

                        training_histories[pid] = ProcessHistory(
                            max_length=HISTORY_LENGTH
                        )

                    training_histories[pid].update(process)

                time.sleep(1)

            feature_vectors = []

            for history_manager in training_histories.values():

                history = history_manager.get(
                    next(iter(history_manager.history))
                ) if history_manager.history else None

                if history is None:
                    continue

                features = self.feature_engineer.process_features(
                    history
                )

                if features is None:
                    continue

                vector = [
                    features["cpu_mean"],
                    features["cpu_max"],
                    features["cpu_std"],
                    features["cpu_recent"],

                    features["memory_mean"],
                    features["memory_max"],
                    features["memory_std"],
                    features["memory_recent"],

                    features["threads_mean"],
                    features["threads_max"],
                    features["threads_recent"],

                    features["cpu_slope"],
                    features["memory_slope"],
                    features["thread_slope"],

                    features["cpu_change"],
                    features["memory_change"],
                    features["thread_change"],

                    features["cpu_volatility"],
                    features["memory_volatility"],
                ]

                feature_vectors.append(vector)

            if len(feature_vectors) >= 10:

                self.model_manager.train(
                    feature_vectors
                )

                self.model_manager.save()

                self.trained = True

        except Exception as exc:

            self.error.emit(
                f"Model training failed: {exc}"
            )

    def process_features_to_vector(self, features):

        return [
            features["cpu_mean"],
            features["cpu_max"],
            features["cpu_std"],
            features["cpu_recent"],

            features["memory_mean"],
            features["memory_max"],
            features["memory_std"],
            features["memory_recent"],

            features["threads_mean"],
            features["threads_max"],
            features["threads_recent"],

            features["cpu_slope"],
            features["memory_slope"],
            features["thread_slope"],

            features["cpu_change"],
            features["memory_change"],
            features["thread_change"],

            features["cpu_volatility"],
            features["memory_volatility"],
        ]

    def collect(self):

        try:

            processes = self.monitor.get_processes(
                limit=PROCESS_LIMIT
            )

            results = []

            for process in processes:

                pid = process["pid"]

                self.history.update(process)

                history = self.history.get(pid)

                if history is None:
                    continue

                features = self.feature_engineer.process_features(
                    history
                )

                if features is None:
                    continue

                if not self.trained:
                    continue

                vector = self.process_features_to_vector(
                    features
                )

                prediction, score = (
                    self.model_manager.predict(vector)
                )

                risk_data = self.risk_engine.calculate(
                    features,
                    score,
                    prediction
                )

                status = (
                    "ANOMALY"
                    if prediction == -1
                    else "NORMAL"
                )

                result = {
                    "pid": pid,
                    "name": process["name"],
                    "status": status,
                    "prediction": prediction,
                    "score": float(score),
                    "risk": risk_data["risk"],
                    "level": risk_data["level"],
                    "cpu": process["cpu"],
                    "memory_percent": process["memory_percent"],
                    "memory_mb": process["memory_mb"],
                    "threads": process["threads"],
                    "features": features,
                }

                results.append(result)

            self.data_ready.emit(results)

        except Exception as exc:

            self.error.emit(
                f"Monitoring error: {exc}"
            )


# ============================================================
# MAIN WINDOW
# ============================================================

class Dashboard(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "AegisOS - AI Security Monitor"
        )

        self.resize(
            1450,
            900
        )

        self.setStyleSheet(
            STYLE
        )

        self.cpu_history = deque(
            maxlen=MAX_CPU_POINTS
        )

        self.memory_history = deque(
            maxlen=MAX_MEMORY_POINTS
        )

        self.last_results = []

        self.setup_ui()

        self.start_worker()

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_monitor
        )

        self.timer.start(
            UPDATE_INTERVAL
        )

    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        main_layout.setSpacing(
            15
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "AEGIS OS"
        )

        title.setObjectName(
            "title"
        )

        subtitle = QLabel(
            "AI-Powered Operating System Security Monitor"
        )

        subtitle.setObjectName(
            "subtitle"
        )

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        header.addLayout(
            title_layout
        )

        header.addStretch()

        self.status_label = QLabel(
            "● SYSTEM ACTIVE"
        )

        self.status_label.setObjectName(
            "status"
        )

        header.addWidget(
            self.status_label
        )

        main_layout.addLayout(
            header
        )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        metrics = QGridLayout()

        self.cpu_value = self.create_metric(
            metrics,
            0,
            0,
            "CPU USAGE"
        )

        self.memory_value = self.create_metric(
            metrics,
            0,
            1,
            "MEMORY USAGE"
        )

        self.process_value = self.create_metric(
            metrics,
            0,
            2,
            "PROCESSES"
        )

        self.anomaly_value = self.create_metric(
            metrics,
            0,
            3,
            "ANOMALIES"
        )

        self.risk_value = self.create_metric(
            metrics,
            0,
            4,
            "HIGH RISK"
        )

        main_layout.addLayout(
            metrics
        )

        # ----------------------------------------------------
        # TABS
        # ----------------------------------------------------

        tabs = QTabWidget()

        tabs.addTab(
            self.create_overview_tab(),
            "Overview"
        )

        tabs.addTab(
            self.create_process_tab(),
            "Processes"
        )

        tabs.addTab(
            self.create_incident_tab(),
            "Incidents"
        )

        main_layout.addWidget(
            tabs
        )

    def create_metric(
        self,
        layout,
        row,
        column,
        title
    ):

        card = QFrame()

        card.setObjectName(
            "card"
        )

        card_layout = QVBoxLayout(
            card
        )

        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "metric_title"
        )

        value_label = QLabel(
            "0"
        )

        value_label.setObjectName(
            "metric_value"
        )

        card_layout.addWidget(
            title_label
        )

        card_layout.addWidget(
            value_label
        )

        layout.addWidget(
            card,
            row,
            column
        )

        return value_label

    # ========================================================
    # OVERVIEW
    # ========================================================

    def create_overview_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )

        # CPU chart

        cpu_card = QFrame()

        cpu_card.setObjectName(
            "card"
        )

        cpu_layout = QVBoxLayout(
            cpu_card
        )

        cpu_title = QLabel(
            "CPU Usage"
        )

        cpu_title.setObjectName(
            "metric_title"
        )

        self.cpu_plot = pg.PlotWidget()

        self.cpu_plot.setBackground(
            "#111827"
        )

        self.cpu_plot.showGrid(
            x=True,
            y=True,
            alpha=0.2
        )

        self.cpu_plot.setYRange(
            0,
            100
        )

        self.cpu_plot.setLabel(
            "left",
            "CPU %"
        )

        self.cpu_plot.setLabel(
            "bottom",
            "Samples"
        )

        self.cpu_curve = (
            self.cpu_plot.plot()
        )

        cpu_layout.addWidget(
            cpu_title
        )

        cpu_layout.addWidget(
            self.cpu_plot
        )

        layout.addWidget(
            cpu_card
        )

        # Memory chart

        memory_card = QFrame()

        memory_card.setObjectName(
            "card"
        )

        memory_layout = QVBoxLayout(
            memory_card
        )

        memory_title = QLabel(
            "Memory Usage"
        )

        memory_title.setObjectName(
            "metric_title"
        )

        self.memory_plot = pg.PlotWidget()

        self.memory_plot.setBackground(
            "#111827"
        )

        self.memory_plot.showGrid(
            x=True,
            y=True,
            alpha=0.2
        )

        self.memory_plot.setLabel(
            "left",
            "Memory %"
        )

        self.memory_plot.setLabel(
            "bottom",
            "Samples"
        )

        self.memory_curve = (
            self.memory_plot.plot()
        )

        memory_layout.addWidget(
            memory_title
        )

        memory_layout.addWidget(
            self.memory_plot
        )

        layout.addWidget(
            memory_card
        )

        return widget

    # ========================================================
    # PROCESS TAB
    # ========================================================

    def create_process_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )

        self.process_table = QTableWidget()

        self.process_table.setColumnCount(
            9
        )

        self.process_table.setHorizontalHeaderLabels(
            [
                "PID",
                "Process",
                "AI",
                "Risk",
                "Level",
                "CPU %",
                "Memory MB",
                "Threads",
                "ML Score",
            ]
        )

        self.process_table.setAlternatingRowColors(
            True
        )

        self.process_table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.process_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        header = (
            self.process_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(
            self.process_table
        )

        return widget

    # ========================================================
    # INCIDENT TAB
    # ========================================================

    def create_incident_tab(self):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )

        controls = QHBoxLayout()

        refresh_button = QPushButton(
            "Refresh Incidents"
        )

        refresh_button.clicked.connect(
            self.load_incidents
        )

        controls.addWidget(
            refresh_button
        )

        controls.addStretch()

        layout.addLayout(
            controls
        )

        self.incident_table = QTableWidget()

        self.incident_table.setColumnCount(
            8
        )

        self.incident_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Timestamp",
                "PID",
                "Status",
                "Risk",
                "Level",
                "Action",
                "Verification",
            ]
        )

        self.incident_table.setAlternatingRowColors(
            True
        )

        self.incident_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        header = (
            self.incident_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.Stretch
        )

        layout.addWidget(
            self.incident_table
        )

        return widget

    # ========================================================
    # WORKER
    # ========================================================

    def start_worker(self):

        self.thread = QThread()

        self.worker = MonitorWorker()

        self.worker.moveToThread(
            self.thread
        )

        self.worker.data_ready.connect(
            self.receive_data
        )

        self.worker.error.connect(
            self.receive_error
        )

        self.thread.started.connect(
            self.train_worker
        )

        self.thread.start()

    def train_worker(self):

        self.status_label.setText(
            "● TRAINING MODEL"
        )

        self.worker.train_model()

        if self.worker.trained:

            self.status_label.setText(
                "● SYSTEM ACTIVE"
            )

    # ========================================================
    # MONITORING
    # ========================================================

    def update_monitor(self):

        if not self.worker.trained:

            return

        self.worker.collect()

    def receive_data(
        self,
        results
    ):

        self.last_results = results

        total_processes = len(
            results
        )

        anomalies = sum(
            1
            for result in results
            if result["status"] == "ANOMALY"
        )

        high_risk = sum(
            1
            for result in results
            if result["risk"] >= 60
        )

        cpu = psutil.cpu_percent(
            interval=None
        )

        memory = psutil.virtual_memory()

        self.cpu_history.append(
            cpu
        )

        self.memory_history.append(
            memory.percent
        )

        # Metrics

        self.cpu_value.setText(
            f"{cpu:.1f}%"
        )

        self.memory_value.setText(
            f"{memory.percent:.1f}%"
        )

        self.process_value.setText(
            str(total_processes)
        )

        self.anomaly_value.setText(
            str(anomalies)
        )

        self.risk_value.setText(
            str(high_risk)
        )

        # Charts

        self.cpu_curve.setData(
            list(self.cpu_history)
        )

        self.memory_curve.setData(
            list(self.memory_history)
        )

        # Process table

        self.update_process_table(
            results
        )

        # Incidents

        self.load_incidents()

    # ========================================================
    # PROCESS TABLE
    # ========================================================

    def update_process_table(
        self,
        results
    ):

        self.process_table.setRowCount(
            len(results)
        )

        for row, result in enumerate(
            results
        ):

            values = [
                result["pid"],
                result["name"],
                result["status"],
                f"{result['risk']:.0f}",
                result["level"],
                f"{result['cpu']:.2f}",
                f"{result['memory_mb']:.2f}",
                f"{result['threads']:.0f}",
                f"{result['score']:.4f}",
            ]

            for column, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(value)
                )

                item.setTextAlignment(
                    Qt.AlignCenter
                )

                self.process_table.setItem(
                    row,
                    column,
                    item
                )

    # ========================================================
    # INCIDENT DATABASE
    # ========================================================

    def load_incidents(self):

        if not DATABASE_PATH.exists():

            return

        try:

            connection = sqlite3.connect(
                DATABASE_PATH
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            )

            tables = [
                row[0]
                for row in cursor.fetchall()
            ]

            incident_table = None

            preferred_names = [
                "incidents",
                "incident_log",
                "incident_logs",
                "events",
                "event_logs",
            ]

            for name in preferred_names:

                if name in tables:

                    incident_table = name

                    break

            if incident_table is None:

                for name in tables:

                    if (
                        "incident" in name.lower()
                        or "event" in name.lower()
                    ):

                        incident_table = name

                        break

            if incident_table is None:

                connection.close()

                return

            cursor.execute(
                f'PRAGMA table_info("{incident_table}")'
            )

            columns = [
                row[1]
                for row in cursor.fetchall()
            ]

            if not columns:

                connection.close()

                return

            cursor.execute(
                f'''
                SELECT *
                FROM "{incident_table}"
                ORDER BY rowid DESC
                LIMIT 100
                '''
            )

            rows = cursor.fetchall()

            connection.close()

            self.incident_table.setRowCount(
                len(rows)
            )

            for row_index, row_data in enumerate(
                rows
            ):

                normalized = {
                    str(columns[i]).lower():
                    row_data[i]
                    for i in range(
                        len(columns)
                    )
                }

                values = [
                    normalized.get(
                        "id",
                        normalized.get(
                            "incident_id",
                            ""
                        )
                    ),

                    normalized.get(
                        "timestamp",
                        ""
                    ),

                    normalized.get(
                        "pid",
                        ""
                    ),

                    normalized.get(
                        "status",
                        normalized.get(
                            "ai_status",
                            ""
                        )
                    ),

                    normalized.get(
                        "risk",
                        normalized.get(
                            "risk_score",
                            ""
                        )
                    ),

                    normalized.get(
                        "level",
                        normalized.get(
                            "risk_level",
                            ""
                        )
                    ),

                    normalized.get(
                        "action",
                        normalized.get(
                            "recovery_action",
                            ""
                        )
                    ),

                    normalized.get(
                        "verification",
                        normalized.get(
                            "verification_status",
                            ""
                        )
                    ),
                ]

                for column, value in enumerate(
                    values
                ):

                    item = QTableWidgetItem(
                        str(value)
                    )

                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                    self.incident_table.setItem(
                        row_index,
                        column,
                        item
                    )

        except Exception:

            pass

    # ========================================================
    # ERROR
    # ========================================================

    def receive_error(
        self,
        message
    ):

        self.status_label.setText(
            "● MONITOR ERROR"
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        self.worker.running = False

        self.thread.quit()

        self.thread.wait(
            3000
        )

        event.accept()


# ============================================================
# APPLICATION
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "AegisOS"
    )

    window = Dashboard()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()