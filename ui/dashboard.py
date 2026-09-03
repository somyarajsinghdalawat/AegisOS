from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QListWidget
)

import pyqtgraph as pg

from collector.system_monitor import SystemMonitor
from collector.process_monitor import ProcessMonitor
from database.database import Database
from detection.process_history import ProcessHistory
from detection.detector import FaultDetector


class Dashboard(QMainWindow):

    def __init__(self):

        super().__init__()

        # ---------------------------------
        # Window configuration
        # ---------------------------------

        self.setWindowTitle(
            "AegisOS - AI Self-Healing System"
        )

        self.resize(1200, 750)

        # ---------------------------------
        # Backend components
        # ---------------------------------

        self.system_monitor = SystemMonitor()

        self.process_monitor = ProcessMonitor()

        self.database = Database()

        self.process_history = ProcessHistory()

        self.detector = FaultDetector()

        self.incidents = []

        # ---------------------------------
        # Graph history
        # ---------------------------------

        self.cpu_history = []

        self.memory_history = []

        self.time_history = []

        # ---------------------------------
        # Create interface
        # ---------------------------------

        self.setup_ui()

        # ---------------------------------
        # Start monitoring timer
        # ---------------------------------

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update_dashboard
        )

        self.timer.start(1000)

        # Initial update
        self.update_dashboard()

    # =================================================
    # USER INTERFACE
    # =================================================

    def setup_ui(self):

        # ---------------------------------
        # Central widget
        # ---------------------------------

        central = QWidget()

        self.setCentralWidget(
            central
        )

        # ---------------------------------
        # Main layout
        # ---------------------------------

        main_layout = QVBoxLayout()

        central.setLayout(
            main_layout
        )

        # ---------------------------------
        # Application title
        # ---------------------------------

        title = QLabel(
            "AEGIS OS"
        )

        title.setStyleSheet(
            "font-size: 28px; "
            "font-weight: bold;"
        )

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "AI-Powered Predictive "
            "Self-Healing System"
        )

        main_layout.addWidget(
            subtitle
        )

        # ---------------------------------
        # System statistics
        # ---------------------------------

        stats_layout = QHBoxLayout()

        self.cpu_label = QLabel(
            "CPU: 0%"
        )

        self.memory_label = QLabel(
            "Memory: 0%"
        )

        self.disk_label = QLabel(
            "Disk: 0%"
        )

        self.os_label = QLabel(
            "OS: Detecting..."
        )

        for label in [
            self.cpu_label,
            self.memory_label,
            self.disk_label,
            self.os_label
        ]:

            label.setStyleSheet(
                "font-size: 18px; "
                "padding: 10px;"
            )

            stats_layout.addWidget(
                label
            )

        main_layout.addLayout(
            stats_layout
        )

        # ---------------------------------
        # Resource graph
        # ---------------------------------

        self.graph = pg.PlotWidget()

        self.graph.setBackground(
            None
        )

        self.graph.setTitle(
            "System Resource Usage"
        )

        self.graph.addLegend()

        self.cpu_curve = self.graph.plot(
            name="CPU"
        )

        self.memory_curve = self.graph.plot(
            name="Memory"
        )

        main_layout.addWidget(
            self.graph
        )

        # ---------------------------------
        # Process table
        # ---------------------------------

        process_title = QLabel(
            "Top Processes"
        )

        process_title.setStyleSheet(
            "font-size: 20px; "
            "font-weight: bold;"
        )

        main_layout.addWidget(
            process_title
        )

        self.process_table = QTableWidget()

        self.process_table.setColumnCount(
            7
        )

        self.process_table.setHorizontalHeaderLabels([
            "PID",
            "Process",
            "Status",
            "CPU %",
            "Memory %",
            "Memory MB",
            "Threads"
        ])

        main_layout.addWidget(
            self.process_table
        )

        # ---------------------------------
        # Fault detection section
        # ---------------------------------

        incident_title = QLabel(
            "AI Fault Detection"
        )

        incident_title.setStyleSheet(
            "font-size: 20px; "
            "font-weight: bold;"
        )

        main_layout.addWidget(
            incident_title
        )

        self.incident_list = QListWidget()

        main_layout.addWidget(
            self.incident_list
        )

    # =================================================
    # DASHBOARD UPDATE
    # =================================================

    def update_dashboard(self):

        # ---------------------------------
        # Get system information
        # ---------------------------------

        system = (
            self.system_monitor
            .get_snapshot()
        )

        # ---------------------------------
        # Get process information
        # ---------------------------------

        processes = (
            self.process_monitor
            .get_processes(
                limit=15
            )
        )

        # ---------------------------------
        # Analyse process behaviour
        # ---------------------------------

        for process in processes:

            # Add current measurement
            # to process history
            self.process_history.update(
                process
            )

            # Get historical measurements
            history = (
                self.process_history
                .get(
                    process["pid"]
                )
            )

            if history:

                # Run fault detection
                detected = (
                    self.detector
                    .detect(
                        process,
                        history
                    )
                )

                # ---------------------------------
                # Process detected incidents
                # ---------------------------------

                for incident in detected:

                    self.incidents.append(
                        incident
                    )

                    # Terminal output
                    print(
                        "[ALERT]",
                        incident["type"],
                        incident["process"],
                        incident["message"]
                    )

                    # GUI output
                    incident_text = (
                        f"[{incident['severity']}] "
                        f"{incident['type']} | "
                        f"{incident['process']} | "
                        f"Risk: "
                        f"{incident['score']:.0f}%"
                    )

                    self.incident_list.insertItem(
                        0,
                        incident_text
                    )

        # ---------------------------------
        # Save monitoring data
        # ---------------------------------

        self.database.save_system_metrics(
            system
        )

        self.database.save_process_metrics(
            processes
        )

        # ---------------------------------
        # Update system statistics
        # ---------------------------------

        self.cpu_label.setText(
            f"CPU: "
            f"{system['cpu']:.1f}%"
        )

        self.memory_label.setText(
            f"Memory: "
            f"{system['memory_percent']:.1f}%"
        )

        self.disk_label.setText(
            f"Disk: "
            f"{system['disk_percent']:.1f}%"
        )

        self.os_label.setText(
            f"OS: "
            f"{system['os']}"
        )

        # ---------------------------------
        # Update graph history
        # ---------------------------------

        self.time_history.append(
            len(self.time_history)
        )

        self.cpu_history.append(
            system["cpu"]
        )

        self.memory_history.append(
            system["memory_percent"]
        )

        # Keep latest 60 readings
        max_points = 60

        self.time_history = (
            self.time_history[
                -max_points:
            ]
        )

        self.cpu_history = (
            self.cpu_history[
                -max_points:
            ]
        )

        self.memory_history = (
            self.memory_history[
                -max_points:
            ]
        )

        # ---------------------------------
        # Update graph
        # ---------------------------------

        self.cpu_curve.setData(
            self.time_history,
            self.cpu_history
        )

        self.memory_curve.setData(
            self.time_history,
            self.memory_history
        )

        # ---------------------------------
        # Update process table
        # ---------------------------------

        self.process_table.setRowCount(
            len(processes)
        )

        for row, process in enumerate(
            processes
        ):

            values = [
                process["pid"],
                process["name"],
                process["status"],
                f"{process['cpu']:.1f}",
                f"{process['memory_percent']:.1f}",
                f"{process['memory_mb']:.1f}",
                process["threads"]
            ]

            for column, value in enumerate(
                values
            ):

                self.process_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        str(value)
                    )
                )
