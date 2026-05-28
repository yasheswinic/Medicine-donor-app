"""Intelligent matching engine with fuzzy search and SQL pre-filtering."""

import time
from typing import Any, Optional

from thefuzz import fuzz

from app.repositories import match_repo, ngo_repo
from app.repositories import donor_repo
from app.utils import detect_medicine_category, get_logger, normalize_location

logger = get_logger()

_match_cache: dict[str, tuple[float, list[dict]]] = {}
CACHE_TTL = 300


def _cache_key(prefix: str, *args) -> str:
    return f"{prefix}:{'|'.join(str(a) for a in args)}"


def _get_cached(key: str) -> Optional[list[dict]]:
    entry = _match_cache.get(key)
    if entry and time.time() - entry[0] < CACHE_TTL:
        return entry[1]
    return None


def _set_cache(key: str, results: list[dict]) -> None:
    _match_cache[key] = (time.time(), results)


def _medicine_compatibility(donor_med: str, donor_cat: str, ngo_meds: str, ngo_prefs: str) -> float:
    med_lower = donor_med.lower()
    ngo_lower = ngo_meds.lower()
    prefs = (ngo_prefs or "general").lower()

    if med_lower in ngo_lower or any(
        token in ngo_lower for token in med_lower.split() if len(token) > 3
    ):
        return 25.0
    if donor_cat in ngo_lower or donor_cat == prefs or prefs == "general":
        return 15.0
    if fuzz.partial_ratio(donor_med, ngo_meds) >= 70:
        return 12.0
    return 0.0


def compute_match_score(donor: dict, ngo: dict) -> tuple[float, str]:
    """
    Score 0-100 with match type.
    City 40%, Locality 35%, Medicine 25%.
    """
    d_city, d_loc = normalize_location(donor["city"], donor["locality"])
    n_city, n_loc = normalize_location(ngo["city"], ngo["locality"])

    city_score = fuzz.ratio(d_city, n_city)
    loc_score = fuzz.token_sort_ratio(d_loc, n_loc)

    donor_cat = donor.get("category") or detect_medicine_category(donor["medicine"])
    med_bonus = _medicine_compatibility(
        donor["medicine"],
        donor_cat,
        ngo["medicines"],
        ngo.get("category_preferences", "general"),
    )

    total = (city_score * 0.40) + (loc_score * 0.35) + med_bonus
    total = min(100.0, total)

    if city_score >= 95 and loc_score >= 90:
        match_type = "exact_match"
    elif total >= 55:
        match_type = "partial_match"
    else:
        match_type = "low_confidence_match"

    return round(total, 1), match_type


def find_matches_for_donor(
    donor: dict, min_score: float = 40.0, persist: bool = True
) -> list[dict]:
    """Find NGO matches for a donor using city pre-filter."""
    cache_key = _cache_key("donor", donor["id"])
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    city_norm, _ = normalize_location(donor["city"], donor["locality"])
    candidates = ngo_repo.get_ngos_by_city(city_norm[:20] if city_norm else donor["city"])
    if not candidates:
        candidates = ngo_repo.get_all_ngos()

    results = []
    for ngo in candidates:
        score, match_type = compute_match_score(donor, ngo)
        if score >= min_score:
            entry = {
                "donor_id": donor["id"],
                "ngo_id": ngo["id"],
                "ngo": ngo,
                "confidence_score": score,
                "match_type": match_type,
            }
            results.append(entry)
            if persist:
                match_repo.upsert_match(
                    donor["id"], ngo["id"], score, match_type
                )

    results.sort(key=lambda x: x["confidence_score"], reverse=True)
    _set_cache(cache_key, results)
    logger.info("Found %d matches for donor %s", len(results), donor["id"])
    return results


def find_matches_for_ngo(
    ngo: dict, min_score: float = 40.0, persist: bool = True
) -> list[dict]:
    """Find donor matches for an NGO using city pre-filter."""
    cache_key = _cache_key("ngo", ngo["id"])
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    city_norm, _ = normalize_location(ngo["city"], ngo["locality"])
    candidates = donor_repo.get_donors_by_city(city_norm[:20] if city_norm else ngo["city"])
    if not candidates:
        candidates = donor_repo.get_all_donors(status="available")

    results = []
    for donor in candidates:
        if donor.get("status") == "expired":
            continue
        score, match_type = compute_match_score(donor, ngo)
        if score >= min_score:
            entry = {
                "donor_id": donor["id"],
                "ngo_id": ngo["id"],
                "donor": donor,
                "confidence_score": score,
                "match_type": match_type,
            }
            results.append(entry)
            if persist:
                match_repo.upsert_match(
                    donor["id"], ngo["id"], score, match_type
                )

    results.sort(key=lambda x: x["confidence_score"], reverse=True)
    _set_cache(cache_key, results)
    return results


def run_bulk_matching(min_score: float = 50.0) -> list[dict]:
    """Recompute all matches — optimized with city grouping."""
    donors = donor_repo.get_all_donors(status="available")
    all_results = []
    city_ngos: dict[str, list] = {}

    for ngo in ngo_repo.get_all_ngos():
        key = normalize_location(ngo["city"], ngo["locality"])[0]
        city_ngos.setdefault(key, []).append(ngo)

    for donor in donors:
        d_city, _ = normalize_location(donor["city"], donor["locality"])
        candidates = city_ngos.get(d_city, []) + ngo_repo.get_ngos_by_city(donor["city"])
        seen = set()
        for ngo in candidates:
            if ngo["id"] in seen:
                continue
            seen.add(ngo["id"])
            score, match_type = compute_match_score(donor, ngo)
            if score >= min_score:
                match_repo.upsert_match(donor["id"], ngo["id"], score, match_type)
                all_results.append(
                    {
                        "donor_id": donor["id"],
                        "ngo_id": ngo["id"],
                        "confidence_score": score,
                        "match_type": match_type,
                    }
                )

    _match_cache.clear()
    logger.info("Bulk matching completed: %d pairs", len(all_results))
    return all_results


def claim_donation(match_id: int) -> None:
    """NGO claims a donation."""
    match_repo.update_match_status(match_id, "claimed")


def update_donation_status(match_id: int, status: str) -> None:
    """Update donation lifecycle status."""
    valid = {"pending", "claimed", "picked_up", "completed", "expired"}
    if status not in valid:
        raise ValueError(f"Invalid status: {status}")
    match_repo.update_match_status(match_id, status)
