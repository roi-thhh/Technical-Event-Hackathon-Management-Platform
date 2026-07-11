"""
database.py — SQLite database initialization, seeding, and connection helper.
"""

import sqlite3
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hackathon.db")


def get_db() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    """Create tables if they don't already exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL CHECK(role IN ('admin', 'judge', 'participant')),
            team_id INTEGER DEFAULT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name VARCHAR(100) UNIQUE NOT NULL,
            github_link VARCHAR(255),
            project_description TEXT DEFAULT NULL,
            screenshot VARCHAR(255) DEFAULT NULL,
            submission_status VARCHAR(20) DEFAULT 'pending',
            grades_published INTEGER DEFAULT 0
        )
    """)

    # Schema migration: alter existing Teams table if columns do not exist
    try:
        cursor.execute("ALTER TABLE Teams ADD COLUMN project_description TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass # Column already exists
    try:
        cursor.execute("ALTER TABLE Teams ADD COLUMN screenshot VARCHAR(255) DEFAULT NULL")
    except sqlite3.OperationalError:
        pass # Column already exists
    try:
        cursor.execute("ALTER TABLE Teams ADD COLUMN event_id INTEGER DEFAULT NULL")
    except sqlite3.OperationalError:
        pass # Column already exists

    # Schema migration: alter existing Users table for profile and event columns
    for col, col_type in [
        ("full_name", "VARCHAR(100) DEFAULT NULL"),
        ("email", "VARCHAR(100) DEFAULT NULL"),
        ("phone", "VARCHAR(20) DEFAULT NULL"),
        ("college", "VARCHAR(150) DEFAULT NULL"),
        ("address", "TEXT DEFAULT NULL"),
        ("linkedin", "VARCHAR(255) DEFAULT NULL"),
        ("github", "VARCHAR(255) DEFAULT NULL"),
        ("event_id", "INTEGER DEFAULT NULL"),
        ("is_lead", "INTEGER DEFAULT 0")
    ]:
        try:
            cursor.execute(f"ALTER TABLE Users ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass # Column already exists

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Evaluations (
            evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            judge_id INTEGER NOT NULL,
            score INTEGER CHECK (score BETWEEN 1 AND 10),
            feedback TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS SystemSettings (
            key VARCHAR(50) PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name VARCHAR(100) NOT NULL,
            event_code VARCHAR(20) UNIQUE NOT NULL,
            judge_invite_code VARCHAR(20) UNIQUE NOT NULL,
            max_team_size INTEGER DEFAULT 4,
            countdown_end VARCHAR(50) DEFAULT NULL,
            submissions_open INTEGER DEFAULT 1,
            grades_published INTEGER DEFAULT 0,
            created_by INTEGER NOT NULL
        )
    """)

    # Seed default settings if empty
    cursor.execute("SELECT COUNT(*) FROM SystemSettings")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO SystemSettings (key, value) VALUES (?, ?)",
            [
                ("event_name", "ToyCad Hackathon 2026"),
                ("team_size_limit", "4"),
                ("submissions_open", "true"),
                ("countdown_end", ""),
                ("grades_published", "false")
            ]
        )

    conn.commit()
    conn.close()


def seed_db():
    """Pre-seed the database with test data (only if Users table is empty)."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM Users")
    count = cursor.fetchone()[0]

    if count == 0:
        # Seed one event
        cursor.execute(
            """
            INSERT INTO Events (event_id, event_name, event_code, judge_invite_code, max_team_size, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (1, "ToyCad Hackathon 2026", "TOYCAD", "JUDGE123", 4, 1)
        )

        # Seed one team
        cursor.execute(
            "INSERT INTO Teams (team_id, team_name, github_link, submission_status, event_id) VALUES (?, ?, ?, ?, ?)",
            (1, "Team Alpha", None, "pending", 1),
        )

        # Seed users: admin, judge, participant (admin1 event_id=1, judge1 event_id=1, participant1 event_id=1, is_lead=1)
        cursor.execute(
            "INSERT INTO Users (user_id, username, password_hash, role, team_id, event_id, is_lead) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, "admin1", hash_password("admin123"), "admin", None, 1, 0)
        )
        cursor.execute(
            "INSERT INTO Users (user_id, username, password_hash, role, team_id, event_id, is_lead) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (2, "judge1", hash_password("judge123"), "judge", None, 1, 0)
        )
        cursor.execute(
            "INSERT INTO Users (user_id, username, password_hash, role, team_id, event_id, is_lead) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (3, "participant1", hash_password("participant123"), "participant", 1, 1, 1)
        )

        conn.commit()
        print("Database seeded with test data.")
    else:
        print("Database already contains data, skipping seed.")

    conn.close()
