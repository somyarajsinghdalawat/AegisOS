import sqlite3
import time


class Database:

    def __init__(self, database_name="aegisos.db"):

        self.connection = sqlite3.connect(
            database_name,
            check_same_thread=False
        )

        self.create_tables()

    def create_tables(self):

        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                os TEXT,
                cpu REAL,
                memory_percent REAL,
                memory_used INTEGER,
                memory_total INTEGER,
                disk_percent REAL,
                disk_used INTEGER,
                disk_total INTEGER,
                network_sent INTEGER,
                network_received INTEGER,
                uptime REAL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS process_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                pid INTEGER,
                name TEXT,
                status TEXT,
                cpu REAL,
                memory_percent REAL,
                memory_mb REAL,
                threads INTEGER
            )
        """)

        self.connection.commit()

    def save_system_metrics(self, data):

        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT INTO system_metrics (
                timestamp,
                os,
                cpu,
                memory_percent,
                memory_used,
                memory_total,
                disk_percent,
                disk_used,
                disk_total,
                network_sent,
                network_received,
                uptime
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["timestamp"],
            data["os"],
            data["cpu"],
            data["memory_percent"],
            data["memory_used"],
            data["memory_total"],
            data["disk_percent"],
            data["disk_used"],
            data["disk_total"],
            data["network_sent"],
            data["network_received"],
            data["uptime"]
        ))

        self.connection.commit()

    def save_process_metrics(self, processes):

        cursor = self.connection.cursor()

        timestamp = time.time()

        for process in processes:

            cursor.execute("""
                INSERT INTO process_metrics (
                    timestamp,
                    pid,
                    name,
                    status,
                    cpu,
                    memory_percent,
                    memory_mb,
                    threads
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                process["pid"],
                process["name"],
                process["status"],
                process["cpu"],
                process["memory_percent"],
                process["memory_mb"],
                process["threads"]
            ))

        self.connection.commit()

    def close(self):

        self.connection.close()