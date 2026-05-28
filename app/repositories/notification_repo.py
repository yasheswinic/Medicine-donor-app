"""In-app notifications (free, no email)."""

from app.db import execute_query, fetch_all
from app.utils import now_iso


def add(recipient: str, title: str, body: str, category: str = "info") -> int:
    return execute_query(
        """
        INSERT INTO notifications (recipient, title, body, category, is_read, created_at)
        VALUES (?, ?, ?, ?, 0, ?)
        """,
        (recipient, title, body, category, now_iso()),
    )


def get_for_recipient(recipient: str, limit: int = 50) -> list[dict]:
    return fetch_all(
        """
        SELECT * FROM notifications WHERE recipient = ?
        ORDER BY created_at DESC LIMIT ?
        """,
        (recipient, limit),
    )


def get_unread_count(recipient: str) -> int:
    from app.db import fetch_one

    row = fetch_one(
        "SELECT COUNT(*) as c FROM notifications WHERE recipient = ? AND is_read = 0",
        (recipient,),
    )
    return row["c"] if row else 0


def mark_read(notification_id: int) -> None:
    execute_query("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))


def mark_all_read(recipient: str) -> None:
    execute_query(
        "UPDATE notifications SET is_read = 1 WHERE recipient = ?", (recipient,)
    )
