import sqlite3
import pandas as pd


class DatasetLoader:

    def __init__(self, database_path="aegisos.db"):
        self.database_path = database_path

    def load_system_metrics(self):

        connection = sqlite3.connect(
            self.database_path
        )

        query = """
            SELECT
                timestamp,
                cpu,
                memory_percent,
                disk_percent,
                network_sent,
                network_received,
                uptime
            FROM system_metrics
            ORDER BY timestamp
        """

        dataframe = pd.read_sql_query(
            query,
            connection
        )

        connection.close()

        return dataframe

    def load_process_metrics(self):

        connection = sqlite3.connect(
            self.database_path
        )

        query = """
            SELECT
                timestamp,
                pid,
                name,
                status,
                cpu,
                memory_percent,
                memory_mb,
                threads
            FROM process_metrics
            ORDER BY timestamp
        """

        dataframe = pd.read_sql_query(
            query,
            connection
        )

        connection.close()

        return dataframe