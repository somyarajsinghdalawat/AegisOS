import json
import sqlite3
import time
from pathlib import Path


class IncidentLogger:
    DB_PATH = Path("aegisos.db")

    def __init__(self):
        self.connection = sqlite3.connect(
            self.DB_PATH,
            check_same_thread=False
        )
        self.connection.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                pid INTEGER NOT NULL,
                process_name TEXT NOT NULL,
                anomaly_score REAL,
                risk_score REAL,
                risk_level TEXT,
                reasons TEXT,
                action TEXT,
                recovery_status TEXT,
                recovery_verification TEXT,
                resolution_timestamp REAL
            )
            """
        )

        self.connection.commit()

    def log_incident(
        self,
        pid,
        process_name,
        anomaly_score,
        risk_score,
        risk_level,
        reasons,
        action="NONE",
        recovery_status="NOT_ATTEMPTED",
        recovery_verification="NOT_VERIFIED",
        resolution_timestamp=None
    ):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO incidents (
                timestamp,
                pid,
                process_name,
                anomaly_score,
                risk_score,
                risk_level,
                reasons,
                action,
                recovery_status,
                recovery_verification,
                resolution_timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                time.time(),
                pid,
                process_name,
                anomaly_score,
                risk_score,
                risk_level,
                json.dumps(reasons),
                action,
                recovery_status,
                recovery_verification,
                resolution_timestamp
            )
        )

        self.connection.commit()

        return cursor.lastrowid

    def update_recovery(
        self,
        incident_id,
        action,
        recovery_status,
        recovery_verification,
        resolution_timestamp=None
    ):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            UPDATE incidents
            SET
                action = ?,
                recovery_status = ?,
                recovery_verification = ?,
                resolution_timestamp = ?
            WHERE id = ?
            """,
            (
                action,
                recovery_status,
                recovery_verification,
                resolution_timestamp,
                incident_id
            )
        )

        self.connection.commit()

    def get_incident(self, incident_id):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM incidents
            WHERE id = ?
            """,
            (incident_id,)
        )

        return cursor.fetchone()

    def get_recent_incidents(self, limit=20):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM incidents
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,)
        )

        return cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None