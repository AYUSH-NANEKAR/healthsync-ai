"""
HealthSync AI - Database Manager

Responsibilities:
    - Open SQLite connections
    - Enable SQLite safety features
    - Initialize a new database
    - Migrate existing databases safely
    - Manage schema versions
    - Provide transaction helpers
    - Provide database health checks

IMPORTANT:
    This file never deletes the user's health database during
    normal initialization or migration.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from database.schema import SCHEMA_SQL, SCHEMA_VERSION


# ============================================================
# DATABASE PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_ROOT / "healthsync.db"


# ============================================================
# DATABASE MANAGER
# ============================================================

class DatabaseManager:
    """
    Central SQLite database manager for HealthSync AI.
    """

    def __init__(
        self,
        database_path: Path | str = DATABASE_PATH,
    ) -> None:

        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ========================================================
    # CONNECTION
    # ========================================================

    def get_connection(self) -> sqlite3.Connection:
        """
        Create a new SQLite connection.

        Each operation receives its own connection.
        This avoids sharing SQLite connections between
        different application components/threads.
        """

        connection = sqlite3.connect(
            self.database_path,
            timeout=10,
        )

        connection.row_factory = sqlite3.Row

        # Foreign-key enforcement.
        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        # Better concurrent read/write behavior.
        connection.execute(
            "PRAGMA journal_mode = WAL"
        )

        # Good balance between durability and performance.
        connection.execute(
            "PRAGMA synchronous = NORMAL"
        )

        return connection

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def initialize(self) -> None:
        """
        Initialize or migrate the database.

        Existing data is preserved.

        New database:
            Create complete schema.

        Existing database:
            Detect version and migrate safely.
        """

        connection = self.get_connection()

        try:
            current_version = self._get_schema_version(
                connection
            )

            # ------------------------------------------------
            # NEW DATABASE
            # ------------------------------------------------

            if current_version == 0:
                self._create_schema(connection)

            # ------------------------------------------------
            # EXISTING DATABASE
            # ------------------------------------------------

            elif current_version < SCHEMA_VERSION:
                self._migrate(
                    connection,
                    current_version,
                    SCHEMA_VERSION,
                )

            # ------------------------------------------------
            # DATABASE ALREADY CURRENT
            # ------------------------------------------------

            elif current_version == SCHEMA_VERSION:
                # Make sure any missing CREATE IF NOT EXISTS
                # objects are restored.
                connection.executescript(SCHEMA_SQL)

            # ------------------------------------------------
            # DATABASE VERSION TOO NEW
            # ------------------------------------------------

            elif current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    "The database was created by a newer version "
                    "of HealthSync AI.\n\n"
                    f"Database version: {current_version}\n"
                    f"Application version: {SCHEMA_VERSION}\n\n"
                    "Please update the application before "
                    "opening this database."
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # CREATE SCHEMA
    # ========================================================

    def _create_schema(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        """
        Create the complete database schema.
        """

        connection.executescript(SCHEMA_SQL)

        self._set_schema_version(
            connection,
            SCHEMA_VERSION,
        )

    # ========================================================
    # SCHEMA VERSION
    # ========================================================

    def _get_schema_version(
        self,
        connection: sqlite3.Connection,
    ) -> int:
        """
        Read the current schema version.

        Returns 0 when the database has not yet been initialized.
        """

        cursor = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name = 'schema_version'
            """
        )

        if cursor.fetchone() is None:
            return 0

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

    def get_schema_version(self) -> int:
        """
        Public method for reading the database schema version.
        """

        connection = self.get_connection()

        try:
            return self._get_schema_version(connection)

        finally:
            connection.close()

    def _set_schema_version(
        self,
        connection: sqlite3.Connection,
        version: int,
    ) -> None:
        """
        Store the schema version.
        """

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            )
            """
        )

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

    def set_schema_version(
        self,
        version: int,
    ) -> None:
        """
        Public method for changing the schema version.
        """

        connection = self.get_connection()

        try:
            self._set_schema_version(
                connection,
                version,
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ========================================================
    # MIGRATION
    # ========================================================

    def _migrate(
        self,
        connection: sqlite3.Connection,
        from_version: int,
        to_version: int,
    ) -> None:
        """
        Safely migrate between database versions.

        Every migration is explicit.

        IMPORTANT:
            Existing user health data is preserved.
        """

        current_version = from_version

        # ----------------------------------------------------
        # VERSION 1 → VERSION 2
        # ----------------------------------------------------

        if current_version < 2 <= to_version:

            self._migrate_v1_to_v2(connection)

            current_version = 2

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        if current_version != to_version:
            raise RuntimeError(
                "Database migration could not reach the "
                f"requested version {to_version}. "
                f"Current version: {current_version}."
            )

        self._set_schema_version(
            connection,
            to_version,
        )

    # ========================================================
    # V1 → V2
    # ========================================================

    def _migrate_v1_to_v2(
        self,
        connection: sqlite3.Connection,
    ) -> None:
        """
        Upgrade the original HealthSync AI database to schema v2.

        Existing tables are preserved.

        New functionality added in v2:
            - Persistent sessions
            - Activity data
            - Device telemetry
            - Location history
            - Blood pressure fields
            - Additional indexes
        """

        # ----------------------------------------------------
        # SESSIONS
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                session_token TEXT NOT NULL UNIQUE,

                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                last_used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                expires_at TEXT,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id
            ON sessions(user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sessions_token
            ON sessions(session_token)
            """
        )

        # ----------------------------------------------------
        # ACTIVITY DATA
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                device_id INTEGER,

                movement TEXT,

                steps INTEGER,

                distance_km REAL,

                calories_kcal REAL,

                active_seconds INTEGER,

                recorded_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                source TEXT,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (device_id)
                    REFERENCES devices(id)
                    ON DELETE SET NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_user_id
            ON activity_data(user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_recorded_at
            ON activity_data(recorded_at)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_activity_user_recorded
            ON activity_data(user_id, recorded_at)
            """
        )

        # ----------------------------------------------------
        # DEVICE TELEMETRY
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS device_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                device_id INTEGER NOT NULL,

                battery_percent REAL,

                recorded_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                source TEXT,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (device_id)
                    REFERENCES devices(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_telemetry_user_id
            ON device_telemetry(user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_telemetry_device_id
            ON device_telemetry(device_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_telemetry_recorded_at
            ON device_telemetry(recorded_at)
            """
        )

        # ----------------------------------------------------
        # LOCATION HISTORY
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS location_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                device_id INTEGER,

                latitude REAL,

                longitude REAL,

                readable_location TEXT,

                accuracy_meters REAL,

                source TEXT,

                recorded_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (device_id)
                    REFERENCES devices(id)
                    ON DELETE SET NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_location_user_id
            ON location_history(user_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_location_recorded_at
            ON location_history(recorded_at)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_location_user_recorded
            ON location_history(user_id, recorded_at)
            """
        )

        # ----------------------------------------------------
        # BLOOD PRESSURE
        #
        # Existing v1 databases may not have these columns.
        # Add them only when necessary.
        # ----------------------------------------------------

        if self._table_exists(
            connection,
            "vitals",
        ):

            columns = self._get_columns(
                connection,
                "vitals",
            )

            if "systolic_pressure" not in columns:
                connection.execute(
                    """
                    ALTER TABLE vitals
                    ADD COLUMN systolic_pressure REAL
                    """
                )

            if "diastolic_pressure" not in columns:
                connection.execute(
                    """
                    ALTER TABLE vitals
                    ADD COLUMN diastolic_pressure REAL
                    """
                )

        # ----------------------------------------------------
        # ENSURE ALL CURRENT SCHEMA OBJECTS EXIST
        # ----------------------------------------------------

        connection.executescript(
            SCHEMA_SQL
        )

    # ========================================================
    # TABLE HELPERS
    # ========================================================

    def _table_exists(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> bool:
        """
        Check whether a SQLite table exists.
        """

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

    def table_exists(
        self,
        table_name: str,
    ) -> bool:
        """
        Public table existence check.
        """

        connection = self.get_connection()

        try:
            return self._table_exists(
                connection,
                table_name,
            )

        finally:
            connection.close()

    def _get_columns(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> set[str]:
        """
        Return all column names for a table.
        """

        cursor = connection.execute(
            f'PRAGMA table_info("{table_name}")'
        )

        return {
            row["name"]
            for row in cursor.fetchall()
        }

    # ========================================================
    # DATABASE HEALTH
    # ========================================================

    def check_connection(self) -> bool:
        """
        Check whether SQLite is accessible.
        """

        connection = None

        try:
            connection = self.get_connection()

            cursor = connection.execute(
                "SELECT 1"
            )

            row = cursor.fetchone()

            return (
                row is not None
                and row[0] == 1
            )

        except sqlite3.Error:
            return False

        finally:
            if connection is not None:
                connection.close()

    def integrity_check(self) -> bool:
        """
        Run SQLite's integrity check.
        """

        connection = self.get_connection()

        try:
            cursor = connection.execute(
                "PRAGMA integrity_check"
            )

            row = cursor.fetchone()

            return (
                row is not None
                and row[0] == "ok"
            )

        finally:
            connection.close()

    # ========================================================
    # TRANSACTION
    # ========================================================

    @contextmanager
    def transaction(
        self,
    ) -> Generator[sqlite3.Connection, None, None]:
        """
        Transaction context manager.

        Automatically commits on success and rolls back when
        an exception occurs.
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
    # CLOSE
    # ========================================================

    def close(self) -> None:
        """
        Compatibility method.

        Connections are created per operation, therefore there
        is no permanent connection to close.
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
    Initialize or safely migrate the default HealthSync AI
    database.
    """

    db.initialize()

    return db


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("HealthSync AI - Database Test")
    print("=" * 60)

    database = initialize_database()

    print()
    print(f"Database path:")
    print(database.database_path)

    print()
    print(
        f"Connection: "
        f"{'OK' if database.check_connection() else 'FAILED'}"
    )

    print(
        f"Integrity: "
        f"{'OK' if database.integrity_check() else 'FAILED'}"
    )

    print(
        f"Schema version: "
        f"{database.get_schema_version()}"
    )

    required_tables = [
        "users",
        "sessions",
        "health_profiles",
        "devices",
        "vitals",
        "activity_data",
        "device_telemetry",
        "location_history",
        "emergency_contacts",
        "ai_reports",
        "health_reports",
        "schema_version",
    ]

    print()
    print("Required tables:")

    all_tables_ok = True

    for table in required_tables:

        exists = database.table_exists(table)

        if not exists:
            all_tables_ok = False

        print(
            f"  {table:<25}"
            f"{'OK' if exists else 'MISSING'}"
        )

    print()

    if all_tables_ok:
        print("Database test: PASSED")
    else:
        print("Database test: FAILED")

    print("=" * 60)