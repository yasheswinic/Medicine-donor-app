"""Legacy schema migration tests."""

import sqlite3

from app.db import init_db


def test_migrate_legacy_donor_schema(test_db, monkeypatch):
    """Simulate monolithic app DB missing status column; init_db must not crash."""
    from app.config import settings

    conn = sqlite3.connect(settings.DB_PATH)
    conn.execute("DROP TABLE IF EXISTS donors")
    conn.execute("""
        CREATE TABLE donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT, phone TEXT, medicine TEXT,
            type TEXT, mfg_date TEXT, city TEXT, locality TEXT, pincode TEXT
        )
    """)
    conn.execute(
        "INSERT INTO donors VALUES (NULL,'A','a@t.com','9876543210','Med','Tablet','2024-01-01','Mumbai','Andheri','400001')"
    )
    conn.commit()
    conn.close()

    init_db()

    conn = sqlite3.connect(settings.DB_PATH)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(donors)")}
    assert "status" in cols
    assert "medicine_type" in cols
    row = conn.execute("SELECT status, medicine_type FROM donors WHERE id=1").fetchone()
    assert row[0] == "available"
    assert row[1] == "Tablet"
    conn.close()
