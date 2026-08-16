"""
HealthSync AI - SQLite Database Schema

Central database schema for:

    - User authentication
    - Persistent login sessions
    - Health profiles
    - BLE/IoT devices
    - Health vitals
    - Activity data
    - Device telemetry
    - Location history
    - Emergency contacts
    - AI reports
    - Health reports

IMPORTANT:
    Sensor values are NOT hardcoded here.

This file only defines the database structure.

Actual values will come from:
    BLE Simulator (temporary)
        OR
    Future ESP32 + real sensors
"""

# ============================================================
# DATABASE VERSION
# ============================================================

SCHEMA_VERSION = 2


# ============================================================
# COMPLETE DATABASE SCHEMA
# ============================================================

SCHEMA_SQL = """

PRAGMA foreign_keys = ON;


-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,

    email TEXT NOT NULL UNIQUE,

    password_hash TEXT NOT NULL,

    phone TEXT,

    date_of_birth TEXT,

    gender TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX IF NOT EXISTS idx_users_email
ON users(email);


-- ============================================================
-- PERSISTENT LOGIN SESSIONS
-- ============================================================

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
);


CREATE INDEX IF NOT EXISTS idx_sessions_user_id
ON sessions(user_id);


CREATE INDEX IF NOT EXISTS idx_sessions_token
ON sessions(session_token);


-- ============================================================
-- HEALTH PROFILE
-- ============================================================

CREATE TABLE IF NOT EXISTS health_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL UNIQUE,

    height REAL,

    weight REAL,

    blood_group TEXT,

    medical_conditions TEXT,

    allergies TEXT,

    medications TEXT,

    emergency_notes TEXT,

    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_health_profiles_user_id
ON health_profiles(user_id);


-- ============================================================
-- DEVICES
-- ============================================================

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    device_name TEXT NOT NULL,

    device_address TEXT,

    device_type TEXT,

    connection_type TEXT DEFAULT 'BLE',

    status TEXT NOT NULL DEFAULT 'Disconnected',

    last_seen TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_devices_user_id
ON devices(user_id);


CREATE INDEX IF NOT EXISTS idx_devices_address
ON devices(device_address);


-- ============================================================
-- HEALTH VITALS
--
-- BLE:
--   Heart Rate
--   SpO2
--   Temperature
--   Blood Pressure
-- ============================================================

CREATE TABLE IF NOT EXISTS vitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    device_id INTEGER,

    heart_rate REAL,

    spo2 REAL,

    temperature REAL,

    systolic_pressure REAL,

    diastolic_pressure REAL,

    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    source TEXT,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (device_id)
        REFERENCES devices(id)
        ON DELETE SET NULL
);


CREATE INDEX IF NOT EXISTS idx_vitals_user_id
ON vitals(user_id);


CREATE INDEX IF NOT EXISTS idx_vitals_recorded_at
ON vitals(recorded_at);


CREATE INDEX IF NOT EXISTS idx_vitals_user_recorded
ON vitals(user_id, recorded_at);


-- ============================================================
-- ACTIVITY DATA
--
-- BLE:
--   Movement
--   Steps
--   Distance
--   Calories
--   Active Time
-- ============================================================

CREATE TABLE IF NOT EXISTS activity_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    device_id INTEGER,

    movement TEXT,

    steps INTEGER,

    distance_km REAL,

    calories_kcal REAL,

    active_seconds INTEGER,

    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    source TEXT,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (device_id)
        REFERENCES devices(id)
        ON DELETE SET NULL
);


CREATE INDEX IF NOT EXISTS idx_activity_user_id
ON activity_data(user_id);


CREATE INDEX IF NOT EXISTS idx_activity_recorded_at
ON activity_data(recorded_at);


CREATE INDEX IF NOT EXISTS idx_activity_user_recorded
ON activity_data(user_id, recorded_at);


-- ============================================================
-- DEVICE TELEMETRY
--
-- BLE:
--   Battery
--
-- This is kept separate from health measurements because
-- battery is a property of the device, not the user.
-- ============================================================

CREATE TABLE IF NOT EXISTS device_telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    device_id INTEGER NOT NULL,

    battery_percent REAL,

    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    source TEXT,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (device_id)
        REFERENCES devices(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_telemetry_user_id
ON device_telemetry(user_id);


CREATE INDEX IF NOT EXISTS idx_telemetry_device_id
ON device_telemetry(device_id);


CREATE INDEX IF NOT EXISTS idx_telemetry_recorded_at
ON device_telemetry(recorded_at);


-- ============================================================
-- LOCATION HISTORY
--
-- BLE simulator currently provides a location value.
--
-- The future ESP32 may provide GPS coordinates if GPS hardware
-- is available.
--
-- The desktop application can also obtain location independently
-- through its Location Service.
-- ============================================================

CREATE TABLE IF NOT EXISTS location_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    device_id INTEGER,

    latitude REAL,

    longitude REAL,

    readable_location TEXT,

    accuracy_meters REAL,

    source TEXT,

    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (device_id)
        REFERENCES devices(id)
        ON DELETE SET NULL
);


CREATE INDEX IF NOT EXISTS idx_location_user_id
ON location_history(user_id);


CREATE INDEX IF NOT EXISTS idx_location_recorded_at
ON location_history(recorded_at);


CREATE INDEX IF NOT EXISTS idx_location_user_recorded
ON location_history(user_id, recorded_at);


-- ============================================================
-- EMERGENCY CONTACTS
-- ============================================================

CREATE TABLE IF NOT EXISTS emergency_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    name TEXT NOT NULL,

    relationship TEXT,

    country_code TEXT,

    phone TEXT NOT NULL,

    is_primary INTEGER NOT NULL DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_emergency_contacts_user_id
ON emergency_contacts(user_id);


-- ============================================================
-- AI REPORTS
-- ============================================================

CREATE TABLE IF NOT EXISTS ai_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    symptoms TEXT NOT NULL,

    analysis TEXT,

    recommendations TEXT,

    severity TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_ai_reports_user_id
ON ai_reports(user_id);


CREATE INDEX IF NOT EXISTS idx_ai_reports_created_at
ON ai_reports(created_at);


-- ============================================================
-- HEALTH REPORTS
-- ============================================================

CREATE TABLE IF NOT EXISTS health_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    title TEXT NOT NULL,

    description TEXT,

    report_type TEXT,

    file_path TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_health_reports_user_id
ON health_reports(user_id);


-- ============================================================
-- SCHEMA VERSION
-- ============================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);


INSERT INTO schema_version (version)
SELECT 2
WHERE NOT EXISTS (
    SELECT 1 FROM schema_version
);


-- ============================================================
-- END OF SCHEMA
-- ============================================================

"""