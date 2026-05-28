"""Free India map — Folium + OpenStreetMap (no API key)."""

from __future__ import annotations

import streamlit as st

from app.utils import normalize_location

# Major Indian cities (lat, lng)
CITY_COORDINATES: dict[str, list[float]] = {
    "bengaluru": [12.9716, 77.5946],
    "bangalore": [12.9716, 77.5946],
    "mumbai": [19.0760, 72.8777],
    "delhi": [28.6139, 77.2090],
    "new delhi": [28.6139, 77.2090],
    "chennai": [13.0827, 80.2707],
    "hyderabad": [17.3850, 78.4867],
    "pune": [18.5204, 73.8567],
    "kolkata": [22.5726, 88.3639],
    "ahmedabad": [23.0225, 72.5714],
    "jaipur": [26.9124, 75.7873],
    "lucknow": [26.8467, 80.9462],
    "surat": [21.1702, 72.8311],
    "nagpur": [21.1458, 79.0882],
    "indore": [22.7196, 75.8577],
    "bhopal": [23.2599, 77.4126],
    "visakhapatnam": [17.6868, 83.2185],
    "patna": [25.5941, 85.1376],
    "vadodara": [22.3072, 73.1812],
    "coimbatore": [11.0168, 76.9558],
    "kochi": [9.9312, 76.2673],
    "thiruvananthapuram": [8.5241, 76.9366],
}


def city_key(city: str) -> str:
    c, _ = normalize_location(city or "", "")
    return c.strip()


def resolve_coords(city: str) -> list[float] | None:
    """Exact match, then fuzzy match against known cities."""
    key = city_key(city)
    if key in CITY_COORDINATES:
        return CITY_COORDINATES[key]

    try:
        from thefuzz import process

        names = list(CITY_COORDINATES.keys())
        match, score = process.extractOne(key, names)
        if match and score >= 75:
            return CITY_COORDINATES[match]
    except Exception:
        pass
    return None


def maps_available() -> bool:
    try:
        import folium  # noqa: F401
        import streamlit_folium  # noqa: F401
        return True
    except ImportError:
        return False


def render_donor_ngo_map(
    donors: list[dict],
    ngos: list[dict],
    matches: list[dict] | None = None,
    height: int = 520,
) -> dict | None:
    """Draw map; returns folium interaction data or None."""
    import folium
    from streamlit_folium import st_folium

    m = folium.Map(location=[22.5, 79.0], zoom_start=5, tiles="OpenStreetMap")

    matched_pairs: set[tuple[int, int]] = set()
    if matches:
        for match in matches:
            if match.get("donor_id") and match.get("ngo_id"):
                matched_pairs.add((match["donor_id"], match["ngo_id"]))

    donor_markers = 0
    for donor in donors:
        coords = resolve_coords(donor.get("city", ""))
        if not coords:
            continue
        donor_markers += 1
        folium.CircleMarker(
            location=coords,
            radius=10,
            popup=folium.Popup(
                f"<b>Donor:</b> {donor.get('name', '—')}<br>"
                f"<b>Medicine:</b> {donor.get('medicine', '—')}<br>"
                f"<b>City:</b> {donor.get('city', '—')}<br>"
                f"<b>Status:</b> {donor.get('status', 'available')}",
                max_width=280,
            ),
            color="#1565c0",
            fill=True,
            fill_color="#42a5f5",
            fill_opacity=0.8,
            tooltip=f"Donor: {donor.get('medicine', '—')} ({donor.get('city')})",
        ).add_to(m)

    ngo_markers = 0
    for ngo in ngos:
        coords = resolve_coords(ngo.get("city", ""))
        if not coords:
            continue
        ngo_markers += 1
        folium.CircleMarker(
            location=coords,
            radius=10,
            popup=folium.Popup(
                f"<b>NGO:</b> {ngo.get('name', '—')}<br>"
                f"<b>Accepts:</b> {ngo.get('medicines', '—')}<br>"
                f"<b>City:</b> {ngo.get('city', '—')}",
                max_width=280,
            ),
            color="#dc2626",
            fill=True,
            fill_color="#f87171",
            fill_opacity=0.8,
            tooltip=f"NGO: {ngo.get('name', '—')}",
        ).add_to(m)

    line_count = 0
    for donor in donors:
        d_coords = resolve_coords(donor.get("city", ""))
        if not d_coords:
            continue
        d_city = city_key(donor.get("city", ""))
        for ngo in ngos:
            if city_key(ngo.get("city", "")) != d_city:
                continue
            n_coords = resolve_coords(ngo.get("city", ""))
            if not n_coords:
                continue
            pair = (donor.get("id"), ngo.get("id"))
            if matches is not None and pair not in matched_pairs:
                continue
            folium.PolyLine(
                [d_coords, n_coords],
                color="#16a34a",
                weight=3,
                opacity=0.6,
            ).add_to(m)
            line_count += 1

    st.caption(
        f"🔵 {donor_markers} donors on map · 🔴 {ngo_markers} NGOs · "
        f"🟢 {line_count} match lines (same city)"
    )
    if donor_markers == 0 and ngo_markers == 0:
        st.warning(
            "No markers yet — use supported city names (e.g. Mumbai, Bengaluru, Delhi, Pune)."
        )

    return st_folium(m, width=None, height=height, returned_objects=[])


def render_live_nearby_map(
    user_lat: float,
    user_lng: float,
    *,
    pharmacies: list[dict],
    nearby_donors: list[dict],
    nearby_ngos: list[dict],
    radius_km: float = 3.0,
    height: int = 560,
) -> dict | None:
    """Map centered on user GPS with pharmacies + app donors/NGOs."""
    import folium
    from folium.plugins import MarkerCluster
    from streamlit_folium import st_folium

    m = folium.Map(location=[user_lat, user_lng], zoom_start=14, tiles="OpenStreetMap")

    folium.Marker(
        [user_lat, user_lng],
        popup="You are here",
        tooltip="Your location",
        icon=folium.Icon(color="green", icon="user", prefix="fa"),
    ).add_to(m)

    folium.Circle(
        radius=radius_km * 1000,
        location=[user_lat, user_lng],
        color="#1565c0",
        fill=True,
        fill_opacity=0.08,
        popup=f"Search radius {radius_km} km",
    ).add_to(m)

    pharma_cluster = MarkerCluster(name="Pharmacies & clinics").add_to(m)
    for p in pharmacies:
        folium.Marker(
            [p["lat"], p["lng"]],
            popup=folium.Popup(
                f"<b>{p.get('name', '—')}</b><br>"
                f"Type: {p.get('type', 'pharmacy')}<br>"
                f"Distance: {p.get('distance_km', '?')} km<br>"
                f"{p.get('address', '')}<br>"
                f"{p.get('opening_hours', '')}",
                max_width=300,
            ),
            tooltip=f"🏪 {p.get('name', 'Shop')} ({p.get('distance_km')} km)",
            icon=folium.Icon(color="orange", icon="plus", prefix="fa"),
        ).add_to(pharma_cluster)

    for donor in nearby_donors:
        if donor.get("lat") is None:
            continue
        folium.CircleMarker(
            [donor["lat"], donor["lng"]],
            radius=9,
            popup=folium.Popup(
                f"<b>Donation:</b> {donor.get('medicine', '—')}<br>"
                f"<b>Donor:</b> {donor.get('name', '—')}<br>"
                f"<b>Distance:</b> {donor.get('distance_km', '?')} km",
                max_width=280,
            ),
            color="#1565c0",
            fill=True,
            fill_color="#42a5f5",
            tooltip=f"💊 {donor.get('medicine', 'Donation')}",
        ).add_to(m)

    for ngo in nearby_ngos:
        if ngo.get("lat") is None:
            continue
        folium.CircleMarker(
            [ngo["lat"], ngo["lng"]],
            radius=9,
            popup=folium.Popup(
                f"<b>NGO:</b> {ngo.get('name', '—')}<br>"
                f"<b>Accepts:</b> {ngo.get('medicines', '—')}<br>"
                f"<b>Distance:</b> {ngo.get('distance_km', '?')} km",
                max_width=280,
            ),
            color="#dc2626",
            fill=True,
            fill_color="#f87171",
            tooltip=f"🏢 {ngo.get('name', 'NGO')}",
        ).add_to(m)

    folium.LayerControl().add_to(m)

    st.caption(
        f"📍 You · 🟠 {len(pharmacies)} real shops (OpenStreetMap) · "
        f"🔵 {len(nearby_donors)} nearby donations · 🔴 {len(nearby_ngos)} NGOs"
    )
    return st_folium(m, width=None, height=height, returned_objects=[])
