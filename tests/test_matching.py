"""Matching engine tests."""

from datetime import date

from app.repositories import donor_repo, ngo_repo
from app.services.matching_service import compute_match_score, find_matches_for_donor


def _seed_donor_ngo():
    donor_id = donor_repo.create_donor({
        "name": "Alice",
        "email": "alice@test.com",
        "phone": "9876543210",
        "medicine": "Paracetamol",
        "medicine_type": "Tablet",
        "quantity": 5,
        "manufacturing_date": str(date.today()),
        "city": "Mumbai",
        "locality": "Andheri",
        "pincode": "400053",
        "category": "painkiller",
    })
    ngo_id = ngo_repo.create_ngo({
        "name": "Help NGO",
        "email": "ngo@test.com",
        "phone": "9123456789",
        "city": "Mumbai",
        "locality": "Andheri",
        "medicines": "paracetamol, ibuprofen",
        "pincode": "400053",
    })
    return donor_repo.get_donor(donor_id), ngo_repo.get_ngo(ngo_id)


def test_exact_match_score():
    donor, ngo = _seed_donor_ngo()
    score, match_type = compute_match_score(donor, ngo)
    assert score >= 70
    assert match_type in ("exact_match", "partial_match")


def test_find_matches_for_donor():
    donor, _ = _seed_donor_ngo()
    matches = find_matches_for_donor(donor, min_score=40, persist=False)
    assert len(matches) >= 1
    assert matches[0]["confidence_score"] > 0


def test_partial_city_match():
    donor, ngo = _seed_donor_ngo()
    ngo["city"] = "Mumbay"
    score, _ = compute_match_score(donor, ngo)
    assert score > 30
