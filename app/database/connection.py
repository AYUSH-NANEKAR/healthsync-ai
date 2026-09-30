from pathlib import Path
import sqlite3


# Project root:
# D:\Projects\HealthSync-AI
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Database:
# D:\Projects\HealthSync-AI\healthsync.db
DATABASE_PATH = PROJECT_ROOT / "healthsync.db"


def get_connection():
    """
    Create and return a connection to the HealthSync SQLite database.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    # Enforce foreign-key relationships in SQLite.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection
