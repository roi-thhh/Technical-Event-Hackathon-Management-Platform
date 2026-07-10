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

    # Schema migration: alter existing Users table for profile columns
    for col, col_type in [
        ("full_name", "VARCHAR(100) DEFAULT NULL"),
        ("email", "VARCHAR(100) DEFAULT NULL"),
        ("phone", "VARCHAR(20) DEFAULT NULL"),
        ("college", "VARCHAR(150) DEFAULT NULL"),
        ("address", "TEXT DEFAULT NULL"),
        ("linkedin", "VARCHAR(255) DEFAULT NULL"),
        ("github", "VARCHAR(255) DEFAULT NULL")
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
        # Seed one team
        cursor.execute(
            "INSERT INTO Teams (team_name, github_link, submission_status) VALUES (?, ?, ?)",
            ("Team Alpha", None, "pending"),
        )

        # Seed users: admin, judge, participant
        users = [
            ("admin1", hash_password("admin123"), "admin", None),
            ("judge1", hash_password("judge123"), "judge", None),
            ("participant1", hash_password("participant123"), "participant", 1),
        ]
        cursor.executemany(
            "INSERT INTO Users (username, password_hash, role, team_id) VALUES (?, ?, ?, ?)",
            users,
        )

        conn.commit()
        print("Database seeded with test data.")
    else:
        print("Database already contains data, skipping seed.")

    conn.close()
