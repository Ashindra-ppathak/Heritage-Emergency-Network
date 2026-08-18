"""
Database utility module for Heritage Emergency Network.
Handles SQLite connection, schema creation, and low-level query helpers.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
DB_PATH = os.path.join(DB_DIR, "heritage.db")


def ensure_db_dir():
    """Make sure the database directory exists."""
    os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_connection():
    """Context-managed SQLite connection with row factory for dict-like access."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT UNIQUE NOT NULL,
    heritage_name TEXT NOT NULL,
    heritage_type TEXT NOT NULL,
    state TEXT NOT NULL,
    district TEXT,
    location TEXT,
    description TEXT,
    issue_type TEXT NOT NULL,
    reported_severity TEXT,
    date_observed TEXT,
    image_path TEXT,
    reporter_id INTEGER,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'SUBMITTED'
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    score INTEGER NOT NULL,
    level TEXT NOT NULL,
    reasons TEXT,
    ai_analysis TEXT,
    source TEXT DEFAULT 'fallback',
    created_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
);

CREATE TABLE IF NOT EXISTS verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    verifier_id TEXT,
    status TEXT NOT NULL,
    notes TEXT,
    verified_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    target_organization TEXT,
    priority TEXT,
    message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
);

CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    assigned_to TEXT,
    status TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
);

CREATE TABLE IF NOT EXISTS monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    risk_score INTEGER,
    condition TEXT,
    notes TEXT,
    next_review TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports (report_id)
);
"""


def init_db():
    """Create all tables if they do not already exist. Safe to call repeatedly."""
    ensure_db_dir()
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def execute(query: str, params: tuple = ()):
    """Run an INSERT/UPDATE/DELETE query."""
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid


def fetch_all(query: str, params: tuple = ()):
    """Run a SELECT query and return list of dict-like rows."""
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def fetch_one(query: str, params: tuple = ()):
    """Run a SELECT query and return a single dict-like row or None."""
    with get_connection() as conn:
        cur = conn.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def db_exists() -> bool:
    return os.path.exists(DB_PATH)
