"""Donor repository — parameterized queries only."""

from typing import Any, Optional

from app.db import execute_query, fetch_all, fetch_one
from app.utils import new_tracking_id, now_iso


def email_exists(email: str) -> bool:
    row = fetch_one("SELECT id FROM donors WHERE email = ?", (email.lower(),))
    return row is not None


def find_recent_similar_donation(
    email: str, medicine: str, days: int = 7
) -> Optional[dict]:
    """Warn if same donor submitted a very similar medicine recently."""
    rows = fetch_all(
        """
        SELECT * FROM donors
        WHERE email = ? AND created_at >= datetime('now', ?)
        ORDER BY id DESC LIMIT 5
        """,
        (email.lower(), f"-{days} days"),
    )
    med_lower = medicine.lower().strip()
    for row in rows:
        existing = (row.get("medicine") or "").lower()
        if med_lower in existing or existing in med_lower:
            return _normalize(row)
    return None


def create_donor(data: dict[str, Any]) -> int:
    ts = now_iso()
    tid = data.get("tracking_id") or new_tracking_id()
    return execute_query(
        """
        INSERT INTO donors (
            name, email, phone, medicine, medicine_type, quantity,
            manufacturing_date, city, locality, pincode, medicine_photo,
            category, status, tracking_id, pickup_address, pickup_time,
            prescription_required, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"],
            data["email"].lower(),
            data["phone"],
            data["medicine"],
            data["medicine_type"],
            data.get("quantity", 1),
            str(data["manufacturing_date"]),
            data["city"],
            data["locality"],
            data["pincode"],
            data.get("medicine_photo"),
            data.get("category", "general"),
            data.get("status", "available"),
            tid,
            data.get("pickup_address"),
            data.get("pickup_time"),
            1 if data.get("prescription_required") else 0,
            ts,
            ts,
        ),
    )


def get_by_email(email: str) -> list[dict]:
    rows = fetch_all(
        "SELECT * FROM donors WHERE email = ? ORDER BY id DESC",
        (email.lower(),),
    )
    return [_normalize(r) for r in rows]


def _normalize(row: Optional[dict]) -> Optional[dict]:
    if not row:
        return row
    if not row.get("medicine_type") and row.get("type"):
        row["medicine_type"] = row["type"]
    if not row.get("manufacturing_date") and row.get("mfg_date"):
        row["manufacturing_date"] = row["mfg_date"]
    row.setdefault("status", "available")
    row.setdefault("quantity", 1)
    return row


def get_donor(donor_id: int) -> Optional[dict]:
    return _normalize(fetch_one("SELECT * FROM donors WHERE id = ?", (donor_id,)))


def get_all_donors(status: Optional[str] = None) -> list[dict]:
    if status:
        rows = fetch_all(
            "SELECT * FROM donors WHERE status = ? ORDER BY id DESC",
            (status,),
        )
    else:
        rows = fetch_all("SELECT * FROM donors ORDER BY id DESC")
    return [_normalize(r) for r in rows]


def get_donors_by_city(city: str) -> list[dict]:
    return fetch_all(
        "SELECT * FROM donors WHERE LOWER(city) LIKE ? AND status = 'available'",
        (f"%{city.lower()}%",),
    )


def update_donor_status(donor_id: int, status: str) -> None:
    execute_query(
        "UPDATE donors SET status = ?, updated_at = ? WHERE id = ?",
        (status, now_iso(), donor_id),
    )


def delete_donor(donor_id: int) -> None:
    execute_query("DELETE FROM donors WHERE id = ?", (donor_id,))


def count_donors() -> int:
    row = fetch_one("SELECT COUNT(*) as cnt FROM donors")
    return row["cnt"] if row else 0


def count_by_status(status: str) -> int:
    row = fetch_one(
        "SELECT COUNT(*) as cnt FROM donors WHERE status = ?", (status,)
    )
    return row["cnt"] if row else 0


def get_all_cities() -> list[str]:
    rows = fetch_all(
        "SELECT DISTINCT city FROM donors UNION SELECT DISTINCT city FROM ngos ORDER BY city"
    )
    return [r["city"] for r in rows if r.get("city")]


def get_donor_counts_by_city() -> dict[str, int]:
    rows = fetch_all("SELECT city, COUNT(*) as cnt FROM donors GROUP BY city")
    return {r["city"]: r["cnt"] for r in rows if r.get("city")}


def get_medicine_type_counts() -> dict[str, int]:
    rows = fetch_all(
        "SELECT COALESCE(medicine_type, 'Other') as mt, COUNT(*) as cnt "
        "FROM donors GROUP BY medicine_type"
    )
    return {r["mt"] or "Other": r["cnt"] for r in rows}
