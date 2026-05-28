"""Landing — clear paths for donors, NGOs, and explorers."""

from datetime import datetime

import streamlit as st

from app.repositories import donor_repo, match_repo, ngo_repo
from app.services.map_service import maps_available
from app.services.matching_service import run_bulk_matching
from app.ui import NAV_MAIN, empty_state, render_footer, render_hero_landing, render_workflow_steps, set_nav


def render() -> None:
    render_hero_landing()

    st.markdown("### What would you like to do?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### I want to donate")
        st.caption("List surplus medicines for NGOs near you.")
        if st.button("Start donation →", type="primary", use_container_width=True):
            set_nav(NAV_MAIN[1])
            st.rerun()
    with c2:
        st.markdown("#### I represent an NGO")
        st.caption("Register and accept nearby donations.")
        if st.button("NGO portal →", use_container_width=True):
            set_nav(NAV_MAIN[3])
            st.rerun()
    with c3:
        st.markdown("#### I want to explore")
        st.caption("See matches, stats, and the map.")
        if st.button("Open dashboard →", use_container_width=True):
            set_nav(NAV_MAIN[4])
            st.rerun()

    c4, c5 = st.columns(2)
    with c4:
        if st.button("🔬 Scan medicine label", use_container_width=True):
            set_nav(NAV_MAIN[2])
            st.rerun()
    with c5:
        if maps_available() and st.button("🗺️ View donation map", use_container_width=True):
            set_nav(NAV_MAIN[5])
            st.rerun()
    if not maps_available():
        st.caption("Install `folium` and `streamlit-folium` to enable the map.")

    st.markdown("---")
    st.markdown("### How it works")
    render_workflow_steps()

    try:
        total = donor_repo.count_donors()
        ngos = ngo_repo.count_ngos()
        completed = donor_repo.count_by_status("completed")
        active = donor_repo.count_by_status("available")
    except Exception as e:
        st.error(str(e))
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Donations", total)
    m2.metric("NGOs", ngos)
    m3.metric("Ready to claim", active)
    m4.metric("Delivered", completed)

    st.markdown("### Recent activity")
    donors = donor_repo.get_all_donors()[:5]
    if donors:
        for d in donors:
            st.markdown(
                f"💊 **{d.get('medicine')}** · {d.get('city')} · "
                f"`{d.get('tracking_id', '—')}` · {d.get('status', 'available')}"
            )
    else:
        empty_state("📭", "No donations yet", "Be the first donor — it takes about 2 minutes.")

    if st.button("🔄 Update all matches", use_container_width=True):
        with st.spinner("Matching…"):
            n = len(run_bulk_matching())
        st.toast(f"{n} pairs updated", icon="✅")

    st.caption(f"Updated {datetime.now().strftime('%d %b %Y %H:%M')}")
    render_footer()
