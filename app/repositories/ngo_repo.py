"""NGO repository."""

from typing import Any, Optional

from app.db import execute_query, fetch_all, fetch_one
from app.utils import now_iso


def email_exists(email: str) -> bool:
    row = fetch_one("SELECT id FROM ngos WHERE email = ?", (email.lower(),))
    return row is not None


def create_ngo(data: dict[str, Any]) -> int:
    ts = now_iso()
    return execute_query(
        """
        INSERT INTO ngos (
            name, email, phone, city, locality, medicines, pincode,
            category_preferences, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"],
            data["email"].lower(),
            data["phone"],
            data["city"],
            data["locality"],
            data["medicines"],
            data["pincode"],
            data.get("category_preferences", "general"),
            ts,
            ts,
        ),
    )


def get_ngo(ngo_id: int) -> Optional[dict]:
    return fetch_one("SELECT * FROM ngos WHERE id = ?", (ngo_id,))


def get_all_ngos() -> list[dict]:
    return fetch_all("SELECT * FROM ngos ORDER BY created_at DESC")


def get_ngos_by_city(city: str) -> list[dict]:
    return fetch_all(
        "SELECT * FROM ngos WHERE LOWER(city) LIKE ?",
        (f"%{city.lower()}%",),
    )


def delete_ngo(ngo_id: int) -> None:
    execute_query("DELETE FROM ngos WHERE id = ?", (ngo_id,))


def count_ngos() -> int:
    row = fetch_one("SELECT COUNT(*) as cnt FROM ngos")
    return row["cnt"] if row else 0
