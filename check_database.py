import sqlite3

connection = sqlite3.connect("aegisos.db")

cursor = connection.cursor()

cursor.execute(
    "SELECT COUNT(*) FROM system_metrics"
)

print(
    "System records:",
    cursor.fetchone()[0]
)

cursor.execute(
    "SELECT COUNT(*) FROM process_metrics"
)

print(
    "Process records:",
    cursor.fetchone()[0]
)

connection.close()