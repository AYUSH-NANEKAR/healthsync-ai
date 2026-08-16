"""
HealthSync AI - SQLite Database Manager

Responsible for:
    - Creating the SQLite database
    - Initializing the schema
    - Managing database connections
    - Enabling foreign-key enforcement
    - Providing safe transaction helpers

Database file:
    healthsync.db
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from database.schema import SCHEMA_SQL, SCHEMA_VERSION


# ============================================================
# DATABASE LOCATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "healthsync.db"


# ============================================================
# DATABASE MANAGER
# ============================================================

class DatabaseManager:
    """
    Central manager for the HealthSync AI SQLite database.

    A single DatabaseManager instance can be shared by services
    throughout the application.
    """

    def __init__(self, database_path: Path | str = DATABASE_PATH) -> None:
        self.database_path = Path(database_path)

        # Make sure the parent directory exists.
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

    # ========================================================
    # CONNECTION
    # ========================================================

    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a new SQLite connection.

        A new connection is returned for each operation/thread
        rather than sharing one connection between threads.
        """

        connection = sqlite3.connect(
            self.database_path,
            timeout=10,
        )

        # Return rows that can be accessed by column name.
        connection.row_factory = sqlite3.Row

        # Enforce foreign-key relationships.
        connection.execute("PRAGMA foreign_keys = ON")

        # Improve SQLite behavior for concurrent read/write access.
        connection.execute("PRAGMA journal_mode = WAL")

        # Keep transactions reasonably durable.
        connection.execute("PRAGMA synchronous = NORMAL")

        return connection

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def initialize(self) -> None:
        """
        Initialize the database.

        Existing data is preserved because the schema uses
        CREATE TABLE IF NOT EXISTS.

        This method is safe to run every time the application
        starts.
        """

        connection = self.get_connection()

        try:
            connection.executescript(SCHEMA_SQL)
            connection.commit()

        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # VERSION
    # ========================================================

    def get_schema_version(self) -> int:
        """
        Return the currently stored database schema version.
        """

        connection = self.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT version
                FROM schema_version
                LIMIT 1
                """
            )

            row = cursor.fetchone()

            if row is None:
                return 0

            return int(row["version"])

        finally:
            connection.close()

    def set_schema_version(self, version: int) -> None:
        """
        Update the stored schema version.
        """

        connection = self.get_connection()

        try:
            connection.execute(
                """
                DELETE FROM schema_version
                """
            )

            connection.execute(
                """
                INSERT INTO schema_version (version)
                VALUES (?)
                """,
                (version,),
            )

            connection.commit()

        except sqlite3.Error:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    def check_connection(self) -> bool:
        """
        Verify that the SQLite database can be opened and queried.
        """

        connection = None

        try:
            connection = self.get_connection()

            cursor = connection.execute(
                "SELECT 1"
            )

            result = cursor.fetchone()

            return result is not None and result[0] == 1

        except sqlite3.Error:
            return False

        finally:
            if connection is not None:
                connection.close()

    # ========================================================
    # TABLE CHECK
    # ========================================================

    def table_exists(self, table_name: str) -> bool:
        """
        Check whether a table exists.

        Only intended for internal application checks.
        """

        connection = self.get_connection()

        try:
            cursor = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name = ?
                """,
                (table_name,),
            )

            return cursor.fetchone() is not None

        finally:
            connection.close()

    # ========================================================
    # TRANSACTION CONTEXT
    # ========================================================

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Provide a connection with automatic transaction handling.

        Example:

            with db.transaction() as connection:
                connection.execute(...)
                connection.execute(...)

        If everything succeeds:
            COMMIT

        If an exception occurs:
            ROLLBACK
        """

        connection = self.get_connection()

        try:
            yield connection
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # CLOSE / COMPATIBILITY
    # ========================================================

    def close(self) -> None:
        """
        No persistent connection is maintained by this manager.

        Connections are opened and closed per operation, so there
        is nothing to close here.

        This method exists to make application shutdown code clean
        and future-proof.
        """

        return None


# ============================================================
# DEFAULT DATABASE INSTANCE
# ============================================================

db = DatabaseManager()


# ============================================================
# INITIALIZATION HELPER
# ============================================================

def initialize_database() -> DatabaseManager:
    """
    Initialize the default database and return its manager.
    """

    db.initialize()

    current_version = db.get_schema_version()

    if current_version != SCHEMA_VERSION:
        db.set_schema_version(SCHEMA_VERSION)

    return db


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":
    print("Initializing HealthSync AI database...")

    database = initialize_database()

    print(f"Database path: {database.database_path}")

    if database.check_connection():
        print("Database connection: OK")
    else:
        print("Database connection: FAILED")

    print(f"Schema version: {database.get_schema_version()}")

    required_tables = [
        "users",
        "health_profiles",
        "vitals",
        "devices",
        "emergency_contacts",
        "ai_reports",
        "health_reports",
    ]

    print("\nDatabase tables:")

    for table in required_tables:
        status = "OK" if database.table_exists(table) else "MISSING"
        print(f"  {table}: {status}")

    print("\nDatabase initialization complete.")