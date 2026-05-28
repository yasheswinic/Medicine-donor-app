"""Global search across donors, NGOs, and matches."""

from app.repositories import donor_repo, match_repo, ngo_repo


def global_search(query: str, limit: int = 25) -> dict[str, list[dict]]:
    """Search all entities; returns grouped results."""
    q = (query or "").strip().lower()
    if len(q) < 2:
        return {"donors": [], "ngos": [], "matches": []}

    donors = [
        d
        for d in donor_repo.get_all_donors()
        if q in " ".join(
            str(d.get(k, ""))
            for k in ("name", "email", "medicine", "city", "locality", "phone")
        ).lower()
    ][:limit]

    ngos = [
        n
        for n in ngo_repo.get_all_ngos()
        if q in " ".join(
            str(n.get(k, ""))
            for k in ("name", "email", "city", "locality", "medicines", "phone")
        ).lower()
    ][:limit]

    matches = match_repo.get_matches_with_details(search=q)[:limit]

    return {"donors": donors, "ngos": ngos, "matches": matches}
