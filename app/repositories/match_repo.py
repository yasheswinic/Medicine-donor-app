"""Match repository."""

from typing import Any, Optional

from app.db import execute_query, fetch_all, fetch_one
from app.utils import now_iso


def upsert_match(
    donor_id: int,
    ngo_id: int,
    confidence: float,
    match_type: str,
    status: str = "pending",
) -> int:
    existing = fetch_one(
        "SELECT id FROM matches WHERE donor_id = ? AND ngo_id = ?",
        (donor_id, ngo_id),
    )
    ts = now_iso()
    if existing:
        execute_query(
            """
            UPDATE matches SET confidence_score = ?, match_type = ?,
            status = ?, updated_at = ? WHERE id = ?
            """,
            (confidence, match_type, status, ts, existing["id"]),
        )
        return existing["id"]
    return execute_query(
        """
        INSERT INTO matches (
            donor_id, ngo_id, confidence_score, match_type, status,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (donor_id, ngo_id, confidence, match_type, status, ts, ts),
    )


def get_matches_with_details(
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> list[dict]:
    query = """
        SELECT m.*, d.name as donor_name, d.medicine, d.city as donor_city,
               d.locality as donor_locality, d.phone as donor_phone,
               d.email as donor_email, d.status as donor_status,
               d.medicine_photo, n.name as ngo_name, n.city as ngo_city,
               n.locality as ngo_locality, n.medicines as ngo_medicines
        FROM matches m
        JOIN donors d ON m.donor_id = d.id
        JOIN ngos n ON m.ngo_id = n.id
        WHERE 1=1
    """
    params: list[Any] = []
    if status:
        query += " AND m.status = ?"
        params.append(status)
    if search:
        query += " AND (d.medicine LIKE ? OR d.name LIKE ? OR n.name LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    query += " ORDER BY m.confidence_score DESC"
    return fetch_all(query, tuple(params))


def update_match_status(match_id: int, status: str) -> None:
    execute_query(
        "UPDATE matches SET status = ?, updated_at = ? WHERE id = ?",
        (status, now_iso(), match_id),
    )
    match = fetch_one("SELECT donor_id FROM matches WHERE id = ?", (match_id,))
    if match and status in ("claimed", "picked_up", "completed"):
        from app.repositories import donor_repo

        donor_repo.update_donor_status(match["donor_id"], status)


def count_matches(match_type: Optional[str] = None) -> int:
    if match_type:
        row = fetch_one(
            "SELECT COUNT(*) as cnt FROM matches WHERE match_type = ?",
            (match_type,),
        )
    else:
        row = fetch_one("SELECT COUNT(*) as cnt FROM matches")
    return row["cnt"] if row else 0


def count_by_status(status: str) -> int:
    row = fetch_one(
        "SELECT COUNT(*) as cnt FROM matches WHERE status = ?", (status,)
    )
    return row["cnt"] if row else 0


def delete_match(match_id: int) -> None:
    execute_query("DELETE FROM matches WHERE id = ?", (match_id,))


def get_cached_matches(donor_id: Optional[int] = None, ngo_id: Optional[int] = None) -> list[dict]:
    if donor_id:
        return fetch_all(
            "SELECT * FROM matches WHERE donor_id = ? ORDER BY confidence_score DESC",
            (donor_id,),
        )
    if ngo_id:
        return fetch_all(
            "SELECT * FROM matches WHERE ngo_id = ? ORDER BY confidence_score DESC",
            (ngo_id,),
        )
    return fetch_all("SELECT * FROM matches ORDER BY confidence_score DESC")
