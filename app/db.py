"""SQLite database layer with parameterized queries only."""

import sqlite3
from contextlib import contextmanager
from typing import Any, Optional

from app.config import settings
from app.utils import get_logger, now_iso

logger = get_logger()

TABLES_SQL = """
CREATE TABLE IF NOT EXISTS donors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    medicine TEXT NOT NULL,
    medicine_type TEXT NOT NULL DEFAULT 'Tablet',
    quantity INTEGER DEFAULT 1,
    manufacturing_date TEXT NOT NULL,
    city TEXT NOT NULL,
    locality TEXT NOT NULL,
    pincode TEXT NOT NULL,
    medicine_photo TEXT,
    category TEXT DEFAULT 'general',
    status TEXT DEFAULT 'available',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ngos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    city TEXT NOT NULL,
    locality TEXT NOT NULL,
    medicines TEXT NOT NULL,
    pincode TEXT NOT NULL,
    category_preferences TEXT DEFAULT 'general',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER NOT NULL,
    ngo_id INTEGER NOT NULL,
    confidence_score REAL NOT NULL,
    match_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (donor_id) REFERENCES donors(id) ON DELETE CASCADE,
    FOREIGN KEY (ngo_id) REFERENCES ngos(id) ON DELETE CASCADE,
    UNIQUE(donor_id, ngo_id)
);

CREATE TABLE IF NOT EXISTS admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    category TEXT DEFAULT 'info',
    is_read INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);
"""

INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_donors_city ON donors(city);
CREATE INDEX IF NOT EXISTS idx_donors_status ON donors(status);
CREATE INDEX IF NOT EXISTS idx_donors_category ON donors(category);
CREATE INDEX IF NOT EXISTS idx_ngos_city ON ngos(city);
CREATE INDEX IF NOT EXISTS idx_matches_donor ON matches(donor_id);
CREATE INDEX IF NOT EXISTS idx_matches_ngo ON matches(ngo_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
"""


@contextmanager
def get_connection():
    """Context-managed SQLite connection with WAL mode."""
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("DB transaction failed: %s", e)
        raise
    finally:
        conn.close()


def execute_query(query: str, params: tuple = ()) -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.lastrowid if cur.lastrowid else cur.rowcount


def fetch_all(query: str, params: tuple = ()) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def fetch_one(query: str, params: tuple = ()) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _add_column(conn: sqlite3.Connection, table: str, col: str, definition: str) -> None:
    if col not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
        logger.info("Migrated %s: added column %s", table, col)


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Upgrade legacy databases (monolithic app schema) safely."""
    ts = now_iso()

    if _table_exists(conn, "donors"):
        cols = _columns(conn, "donors")

        if "type" in cols:
            _add_column(conn, "donors", "medicine_type", "TEXT")
            conn.execute(
                "UPDATE donors SET medicine_type = type "
                "WHERE medicine_type IS NULL OR medicine_type = ''"
            )
        else:
            _add_column(conn, "donors", "medicine_type", "TEXT DEFAULT 'Tablet'")

        if "mfg_date" in cols:
            _add_column(conn, "donors", "manufacturing_date", "TEXT")
            conn.execute(
                "UPDATE donors SET manufacturing_date = mfg_date "
                "WHERE manufacturing_date IS NULL OR manufacturing_date = ''"
            )
        else:
            _add_column(conn, "donors", "manufacturing_date", "TEXT DEFAULT ''")

        for col, defn in (
            ("quantity", "INTEGER DEFAULT 1"),
            ("medicine_photo", "TEXT"),
            ("category", "TEXT DEFAULT 'general'"),
            ("status", "TEXT DEFAULT 'available'"),
            ("created_at", "TEXT"),
            ("updated_at", "TEXT"),
        ):
            _add_column(conn, "donors", col, defn)

        conn.execute(
            "UPDATE donors SET status = 'available' WHERE status IS NULL OR status = ''"
        )
        conn.execute(
            "UPDATE donors SET created_at = ? WHERE created_at IS NULL OR created_at = ''",
            (ts,),
        )
        conn.execute(
            "UPDATE donors SET updated_at = ? WHERE updated_at IS NULL OR updated_at = ''",
            (ts,),
        )
        conn.execute(
            "UPDATE donors SET manufacturing_date = ? "
            "WHERE manufacturing_date IS NULL OR manufacturing_date = ''",
            (ts[:10],),
        )

    if _table_exists(conn, "ngos"):
        _add_column(conn, "ngos", "email", "TEXT")
        _add_column(conn, "ngos", "phone", "TEXT DEFAULT ''")
        _add_column(conn, "ngos", "category_preferences", "TEXT DEFAULT 'general'")
        _add_column(conn, "ngos", "created_at", "TEXT")
        _add_column(conn, "ngos", "updated_at", "TEXT")

        conn.execute(
            "UPDATE ngos SET email = 'ngo' || id || '@demo.local' "
            "WHERE email IS NULL OR email = ''"
        )
        conn.execute(
            "UPDATE ngos SET created_at = ? WHERE created_at IS NULL OR created_at = ''",
            (ts,),
        )
        conn.execute(
            "UPDATE ngos SET updated_at = ? WHERE updated_at IS NULL OR updated_at = ''",
            (ts,),
        )

    if _table_exists(conn, "matches"):
        _add_column(conn, "matches", "status", "TEXT DEFAULT 'pending'")
        _add_column(conn, "matches", "created_at", "TEXT")
        _add_column(conn, "matches", "updated_at", "TEXT")
        conn.execute(
            "UPDATE matches SET status = 'pending' WHERE status IS NULL OR status = ''"
        )

    if _table_exists(conn, "donors"):
        for col, defn in (
            ("tracking_id", "TEXT"),
            ("pickup_address", "TEXT"),
            ("pickup_time", "TEXT"),
            ("prescription_required", "INTEGER DEFAULT 0"),
        ):
            _add_column(conn, "donors", col, defn)

    if _table_exists(conn, "ngos"):
        _add_column(conn, "ngos", "license_number", "TEXT")
        _add_column(conn, "ngos", "is_verified", "INTEGER DEFAULT 1")


def init_db() -> None:
    """Create tables, migrate legacy schema, then add indexes."""
    with get_connection() as conn:
        conn.executescript(TABLES_SQL)
        _migrate_schema(conn)
        try:
            conn.executescript(INDEXES_SQL)
        except sqlite3.OperationalError as e:
            logger.error("Index creation failed: %s", e)
            raise

    from app.config import settings
    from app.services.auth_service import bootstrap_admin_from_env

    bootstrap_admin_from_env(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
    logger.info("Database ready at %s", settings.DB_PATH)
