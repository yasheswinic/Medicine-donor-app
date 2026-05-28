"""Match dashboard — cards, map, analytics, lifecycle actions."""

from datetime import datetime

import pandas as pd
import streamlit as st

from app.constants import APP_ROOT
from app.repositories import donor_repo, match_repo, ngo_repo
from app.services.map_service import maps_available, render_donor_ngo_map
from app.services.matching_service import claim_donation, run_bulk_matching, update_donation_status
from app.ui import (
    NAV_MAIN,
    confidence_badge,
    donor_status_pill,
    empty_state,
    render_breadcrumb,
    render_page_header,
    status_badge,
)

PAGE_SIZE = 6


def _filter_matches(
    matches: list[dict],
    status_filters: list[str],
    city_filter: str,
    search: str,
) -> list[dict]:
    out = matches
    if status_filters:
        out = [m for m in out if m.get("status") in status_filters]
    if city_filter and city_filter != "All":
        out = [
            m for m in out
            if city_filter.lower() in (m.get("donor_city") or "").lower()
        ]
    if search:
        q = search.lower()
        out = [
            m for m in out
            if q in f"{m.get('donor_name','')} {m.get('ngo_name','')} {m.get('medicine','')}".lower()
        ]
    return out


def render() -> None:
    render_page_header(
        "Match Dashboard",
        "Track matches, update status, and explore analytics",
        "📊",
    )
    render_breadcrumb("Home", "Dashboard")

    try:
        all_matches = match_repo.get_matches_with_details()
        donors = donor_repo.get_all_donors()
        ngos = ngo_repo.get_all_ngos()
        cities = ["All"] + donor_repo.get_all_cities()
    except Exception as e:
        st.error(f"Could not load data: {e}")
        return

    f1, f2, f3, f4 = st.columns([2, 2, 1, 1])
    with f1:
        status_filters = st.multiselect(
            "Filter by status",
            ["pending", "claimed", "picked_up", "completed", "expired", "available"],
            default=["pending", "claimed"],
        )
    with f2:
        city_filter = st.selectbox("Filter by city", cities)
    with f3:
        search = st.text_input("Search", placeholder="Donor, NGO, medicine")
    with f4:
        if st.button("🔄 Refresh matches", use_container_width=True):
            with st.spinner("Running matcher…"):
                run_bulk_matching()
            st.toast("Matches updated", icon="✅")
            st.rerun()

    matches = _filter_matches(all_matches, status_filters, city_filter, search)
    matches.sort(key=lambda m: m.get("confidence_score", 0), reverse=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matches shown", len(matches))
    m2.metric(
        "Avg confidence",
        f"{sum(m['confidence_score'] for m in matches) / len(matches):.0f}%"
        if matches else "—",
    )
    m3.metric("Donors", len(donors))
    m4.metric("NGOs", len(ngos))

    tab_cards, tab_map, tab_analytics = st.tabs(
        ["🗂️ Match cards", "🗺️ Map view", "📈 Analytics"]
    )

    with tab_analytics:
        c1, c2 = st.columns(2)
        city_counts = donor_repo.get_donor_counts_by_city()
        if city_counts:
            c1.markdown("##### Donations by city")
            c1.bar_chart(city_counts)
        type_counts = donor_repo.get_medicine_type_counts()
        if type_counts:
            try:
                import plotly.express as px

                fig = px.pie(
                    values=list(type_counts.values()),
                    names=list(type_counts.keys()),
                    title="Donations by medicine type",
                    color_discrete_sequence=["#1565c0", "#42a5f5", "#90caf9", "#64b5f6"],
                    hole=0.45,
                )
                fig.update_layout(margin=dict(t=40, b=20, l=20, r=20), height=320)
                c2.plotly_chart(fig, use_container_width=True)
            except ImportError:
                c2.bar_chart(type_counts)
                c2.caption("Install plotly for donut chart: pip install plotly")

        if matches:
            st.download_button(
                "📥 Export filtered matches (CSV)",
                pd.DataFrame(matches).to_csv(index=False).encode(),
                f"matches_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv",
                use_container_width=True,
            )

    with tab_map:
        if not maps_available():
            st.warning("Install map: `pip install folium streamlit-folium`")
            if st.button("Open full Map page →"):
                from app.ui import set_nav
                set_nav("🗺️ Map")
                st.rerun()
        elif not donors and not ngos:
            st.info("Add donors and NGOs to see the map.")
        else:
            try:
                render_donor_ngo_map(donors, ngos, matches if matches else all_matches)
            except Exception as ex:
                st.error(str(ex))
            if st.button("Open larger map view →"):
                from app.ui import set_nav
                set_nav("🗺️ Map")
                st.rerun()

    with tab_cards:
        if not matches:
            empty_state(
                "🤝",
                "No matches found",
                "Adjust filters or register more donors and NGOs.",
                "Go to Donor Panel",
                NAV_MAIN[1],
            )
            return

        total_pages = max(1, (len(matches) + PAGE_SIZE - 1) // PAGE_SIZE)
        page = st.number_input(
            "Page", min_value=1, max_value=total_pages, value=1, key="dash_page"
        )
        start = (page - 1) * PAGE_SIZE
        page_matches = matches[start : start + PAGE_SIZE]
        st.caption(f"Showing {start + 1}–{min(start + PAGE_SIZE, len(matches))} of {len(matches)}")

        for m in page_matches:
            donor_status = m.get("donor_status") or "available"
            st.markdown('<div class="match-card">', unsafe_allow_html=True)
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{m['donor_name']}** → **{m['ngo_name']}**")
                st.caption(f"💊 {m['medicine']} · 📍 {m['donor_locality']}, {m['donor_city']}")
                st.markdown(confidence_badge(m["confidence_score"], m["match_type"]), unsafe_allow_html=True)
                st.markdown(
                    f"Match: {status_badge(m.get('status', 'pending'))} · "
                    f"Donor: {donor_status_pill(donor_status)}",
                    unsafe_allow_html=True,
                )
            with c2:
                photo = m.get("medicine_photo")
                if photo:
                    path = APP_ROOT / photo
                    if path.exists():
                        st.image(str(path), width=72)

            a1, a2, a3 = st.columns(3)
            mid = m["id"]
            did = m.get("donor_id")

            if a1.button("✅ Mark claimed", key=f"claim_{mid}", use_container_width=True):
                claim_donation(mid)
                st.toast("Marked as claimed", icon="✅")
                st.rerun()
            if a2.button("📦 Mark completed", key=f"done_{mid}", use_container_width=True):
                update_donation_status(mid, "completed")
                st.toast("Marked as completed", icon="✅")
                st.rerun()
            if a3.button("❌ Remove match", key=f"rm_{mid}", use_container_width=True):
                match_repo.delete_match(mid)
                st.toast("Match removed", icon="🗑️")
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
