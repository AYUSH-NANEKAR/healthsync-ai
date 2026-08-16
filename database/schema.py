"""
HealthSync AI - SQLite Database Schema

Contains the SQL schema used to initialize the HealthSync AI database.

Database:
    healthsync.db

Important:
    - User data is isolated using user_id.
    - Passwords are stored as hashes, never plaintext.
    - Foreign keys are enabled by the database layer.
    - Schema creation must never delete existing user data.
"""


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
-- HEALTH PROFILES
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
-- VITALS
-- ============================================================

CREATE TABLE IF NOT EXISTS vitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    device_id INTEGER,

    heart_rate REAL,

    spo2 REAL,

    temperature REAL,

    steps INTEGER,

    movement TEXT,

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
-- DEVICES
-- ============================================================

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    device_name TEXT NOT NULL,

    device_address TEXT,

    device_type TEXT,

    connection_type TEXT,

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
-- DATABASE VERSION
-- ============================================================

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);


INSERT INTO schema_version (version)
SELECT 1
WHERE NOT EXISTS (
    SELECT 1 FROM schema_version
);
"""


SCHEMA_VERSION = 1