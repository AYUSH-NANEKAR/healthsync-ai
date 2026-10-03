from app.database.connection import get_connection


def initialize_database():
    """
    Create and maintain all HealthSync AI database tables.

    Existing user/device/telemetry data is preserved.
    Health profiles are stored separately for each user.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # ============================================================
        # USERS
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ------------------------------------------------------------
        # Migration safety:
        # If an older users table exists without "name", add it.
        # ------------------------------------------------------------
        cursor.execute("PRAGMA table_info(users)")
        user_columns = {
            column[1]
            for column in cursor.fetchall()
        }

        if "name" not in user_columns:
            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN name TEXT NOT NULL DEFAULT ''
                """
            )

        # ============================================================
        # SESSIONS
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT NOT NULL UNIQUE,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ============================================================
        # HEALTH PROFILES
        # One profile belongs to exactly one user.
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS health_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,

                mobile_number TEXT,
                date_of_birth TEXT,
                gender TEXT,
                blood_group TEXT,

                height REAL,
                weight REAL,

                city TEXT,

                allergies TEXT,
                medical_conditions TEXT,
                medications TEXT,

                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ============================================================
        # EMERGENCY CONTACTS
        # Multiple emergency contacts can belong to one user.
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS emergency_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,

                contact_name TEXT NOT NULL,
                relationship TEXT,
                phone_number TEXT NOT NULL,

                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ============================================================
        # DEVICES
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_name TEXT NOT NULL,
                device_address TEXT,
                device_type TEXT NOT NULL,
                connection_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'DISCONNECTED',
                service_uuid TEXT,
                last_seen_at DATETIME,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ============================================================
        # VITALS
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_id INTEGER NOT NULL,

                heart_rate INTEGER,
                spo2 INTEGER,
                temperature REAL,
                systolic_bp INTEGER,
                diastolic_bp INTEGER,

                recorded_at DATETIME NOT NULL,
                source TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (device_id)
                    REFERENCES devices(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ============================================================
        # ACTIVITY DATA
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_id INTEGER NOT NULL,

                movement TEXT,
                steps INTEGER,
                distance REAL,
                calories REAL,
                active_time INTEGER,

                recorded_at DATETIME NOT NULL,
                source TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (device_id)
                    REFERENCES devices(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ============================================================
        # DEVICE TELEMETRY
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS device_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,

                battery INTEGER,
                recorded_at DATETIME NOT NULL,

                FOREIGN KEY (device_id)
                    REFERENCES devices(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ============================================================
        # LOCATION HISTORY
        # ============================================================
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS location_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_id INTEGER NOT NULL,

                readable_name TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,

                recorded_at DATETIME NOT NULL,
                source TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (device_id)
                    REFERENCES devices(id)
                    ON DELETE CASCADE
            )
            """
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
