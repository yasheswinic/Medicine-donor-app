"""Map — India overview + live nearby tracking (free OSM)."""

import streamlit as st

from app.components.geolocation import request_live_location
from app.repositories import donor_repo, match_repo, ngo_repo
from app.services.location_service import (
    fetch_nearby_places,
    geocode_pincode,
    nearby_app_records,
    reverse_geocode,
)
from app.services.map_service import maps_available, render_donor_ngo_map, render_live_nearby_map
from app.services.matching_service import run_bulk_matching
from app.ui import empty_state, render_breadcrumb, render_page_header


def _render_overview_map() -> None:
    donors = donor_repo.get_all_donors()
    ngos = ngo_repo.get_all_ngos()
    matches = match_repo.get_matches_with_details()

    if not donors and not ngos:
        empty_state(
            "🗺️",
            "Map is empty",
            "Register a donation or NGO first, then come back here.",
            "Donate medicines",
            "💊 Donate Medicines",
        )
        return

    c1, c2, c3 = st.columns(3)
    show_donors = c1.checkbox("Show donors", value=True, key="map_show_donors")
    show_ngos = c2.checkbox("Show NGOs", value=True, key="map_show_ngos")
    show_lines = c3.checkbox("Show match lines", value=True, key="map_show_lines")

    city_filter = st.selectbox(
        "Focus city",
        ["All India"] + donor_repo.get_all_cities(),
        key="map_city_filter",
    )

    if st.button("🔄 Refresh matches before map", key="map_refresh_matches"):
        run_bulk_matching()
        matches = match_repo.get_matches_with_details()
        st.toast("Matches updated", icon="✅")

    d_list = donors if show_donors else []
    n_list = ngos if show_ngos else []
    if city_filter != "All India":
        d_list = [d for d in d_list if city_filter.lower() in (d.get("city") or "").lower()]
        n_list = [n for n in n_list if city_filter.lower() in (n.get("city") or "").lower()]

    with st.spinner("Loading map…"):
        try:
            render_donor_ngo_map(d_list, n_list, matches if show_lines else None, height=520)
        except Exception as ex:
            st.error(f"Could not render map: {ex}")


def _render_live_nearby() -> None:
    st.markdown(
        "Use **live GPS** or a **pincode** to find real pharmacies/clinics on OpenStreetMap "
        "and donations/NGOs registered in this app nearby. **100% free** — no Google API key."
    )

    if "user_location" not in st.session_state:
        st.session_state.user_location = None

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("📍 Use my live location", type="primary", use_container_width=True):
            st.session_state._geo_pending = True
    with c2:
        pincode = st.text_input("Or enter pincode", placeholder="e.g. 400053", key="live_pincode")
        if st.button("Find by pincode", use_container_width=True):
            geo = geocode_pincode(pincode)
            if geo:
                st.session_state.user_location = geo
                st.toast(f"Located: {geo.get('display_name', pincode)}", icon="📍")
                st.rerun()
            else:
                st.error("Could not geocode that pincode.")
    with c3:
        radius_km = st.slider("Search radius (km)", 1, 15, 5, key="live_radius")

    if st.session_state.get("_geo_pending"):
        st.info("Allow **location access** in your browser when prompted.")
        loc = request_live_location()
        if loc:
            st.session_state._geo_pending = False
            if loc.get("error"):
                st.error(loc["error"])
            else:
                place = reverse_geocode(loc["lat"], loc["lng"])
                st.session_state.user_location = {
                    **loc,
                    "display_name": place or "Your GPS location",
                    "source": "gps",
                }
                st.rerun()

    loc = st.session_state.user_location
    if not loc:
        st.warning("Set your location with **live GPS** or **pincode** to see nearby shops and donations.")
        return

    lat, lng = loc["lat"], loc["lng"]
    st.success(f"📍 **{loc.get('display_name', 'Your location')}** ({lat:.4f}, {lng:.4f})")
    if loc.get("accuracy_m"):
        st.caption(f"GPS accuracy ~{loc['accuracy_m']} m")

    radius_m = int(radius_km * 1000)

    with st.spinner("Finding nearby pharmacies & clinics (OpenStreetMap)…"):
        places, places_err = fetch_nearby_places(lat, lng, radius_m=radius_m)

    donors = donor_repo.get_all_donors()
    ngos = ngo_repo.get_all_ngos()
    with st.spinner("Matching app donations & NGOs near you…"):
        nearby = nearby_app_records(lat, lng, donors, ngos, radius_km=float(radius_km))

    if places_err:
        st.warning(places_err)
    if not places and not nearby["donors"] and not nearby["ngos"]:
        st.info("Nothing found in this radius — try increasing search radius.")

    try:
        render_live_nearby_map(
            lat,
            lng,
            pharmacies=places,
            nearby_donors=nearby["donors"],
            nearby_ngos=nearby["ngos"],
            radius_km=float(radius_km),
        )
    except Exception as ex:
        st.error(f"Map error: {ex}")

    t1, t2, t3 = st.tabs(["🏪 Real shops", "💊 Nearby donations", "🏢 Nearby NGOs"])

    with t1:
        if not places:
            st.caption("No pharmacies/clinics in OpenStreetMap for this area — data varies by region.")
        for p in places[:15]:
            with st.container(border=True):
                st.markdown(f"**{p['name']}** · {p['type']} · **{p['distance_km']} km**")
                if p.get("address"):
                    st.caption(p["address"])
                if p.get("opening_hours"):
                    st.caption(f"Hours: {p['opening_hours']}")

    with t2:
        for d in nearby["donors"][:15]:
            st.markdown(
                f"**{d.get('medicine')}** — {d.get('city')} · "
                f"`{d.get('tracking_id', '')}` · **{d.get('distance_km')} km**"
            )
        if not nearby["donors"]:
            st.caption("No donations in the app within this radius yet.")

    with t3:
        for n in nearby["ngos"][:15]:
            st.markdown(f"**{n.get('name')}** — {n.get('city')} · **{n.get('distance_km')} km**")
        if not nearby["ngos"]:
            st.caption("No NGOs in the app within this radius yet.")


def render() -> None:
    render_page_header(
        "Donation Map",
        "India overview + live nearby shops & medicine tracking",
        "🗺️",
    )
    render_breadcrumb("Home", "Map")

    if not maps_available():
        st.error("Map packages missing. Run in your terminal:")
        st.code("pip install folium streamlit-folium")
        return

    tab_overview, tab_live = st.tabs(["🗺️ India overview", "📍 Live nearby"])

    with tab_overview:
        _render_overview_map()
        with st.expander("Supported cities (examples)"):
            st.write(
                "Mumbai, Delhi, Bengaluru/Bangalore, Chennai, Hyderabad, Pune, Kolkata, "
                "Ahmedabad, Jaipur, Lucknow, Surat, Nagpur, Indore, Kochi, and more."
            )

    with tab_live:
        _render_live_nearby()
