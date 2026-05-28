"""Database layer tests."""

from datetime import date

from app.db import execute_query, fetch_all, fetch_one, init_db
from app.repositories import donor_repo, match_repo, ngo_repo


def test_init_db():
    init_db()
    row = fetch_one("SELECT name FROM sqlite_master WHERE type='table' AND name='donors'")
    assert row is not None


def test_parameterized_insert():
    donor_id = donor_repo.create_donor({
        "name": "Test User",
        "email": "testuser@example.com",
        "phone": "9876543210",
        "medicine": "Aspirin",
        "medicine_type": "Tablet",
        "quantity": 1,
        "manufacturing_date": str(date.today()),
        "city": "Pune",
        "locality": "Kothrud",
        "pincode": "411038",
    })
    d = donor_repo.get_donor(donor_id)
    assert d["email"] == "testuser@example.com"


def test_duplicate_email_blocked():
    data = {
        "name": "A",
        "email": "dup@example.com",
        "phone": "9876543210",
        "medicine": "Med",
        "medicine_type": "Tablet",
        "manufacturing_date": str(date.today()),
        "city": "X",
        "locality": "Y",
        "pincode": "400001",
    }
    donor_repo.create_donor(data)
    assert donor_repo.email_exists("dup@example.com")


def test_match_upsert():
    d_id = donor_repo.create_donor({
        "name": "D",
        "email": "d@ex.com",
        "phone": "9876543210",
        "medicine": "M",
        "medicine_type": "Tablet",
        "manufacturing_date": str(date.today()),
        "city": "A",
        "locality": "B",
        "pincode": "400001",
    })
    n_id = ngo_repo.create_ngo({
        "name": "N",
        "email": "n@ex.com",
        "phone": "9123456789",
        "city": "A",
        "locality": "B",
        "medicines": "M",
        "pincode": "400001",
    })
    match_repo.upsert_match(d_id, n_id, 85.0, "exact_match")
    matches = fetch_all("SELECT * FROM matches WHERE donor_id = ?", (d_id,))
    assert len(matches) == 1
