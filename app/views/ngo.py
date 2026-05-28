"""NGO portal — registration, incoming donations, inventory, analytics."""

import pandas as pd
import streamlit as st

from app.constants import MEDICINE_CATEGORIES
from app.repositories import donor_repo, match_repo, ngo_repo
from app.repositories.notification_repo import add as notify
from app.services.matching_service import find_matches_for_ngo, update_donation_status
from app.services.matching_service import claim_donation
from app.services.validation_service import validate_ngo
from app.ui import (
    confidence_badge,
    donor_status_pill,
    empty_state,
    render_breadcrumb,
    render_page_header,
    render_timeline,
)


def render() -> None:
    render_page_header(
        "NGO Portal",
        "Register, accept donations, and track deliveries",
        "🏢",
    )
    render_breadcrumb("Home", "NGO")

    tab_reg, tab_dash = st.tabs(["Registration", "NGO dashboard"])

    with tab_reg:
        with st.form("ngo_reg"):
            st.markdown("#### Organization details")
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("NGO name *")
                license = st.text_input("License / registration no. *")
                email = st.text_input("Email *")
            with c2:
                phone = st.text_input("Phone *")
                city = st.text_input("City *")
                locality = st.text_input("Areas served (locality) *")
            medicines = st.text_input("Accepted medicines (comma-separated) *")
            pincode = st.text_input("Pincode *")
            prefs = st.selectbox("Category focus", MEDICINE_CATEGORIES)
            verified = st.checkbox("I confirm our organization is authorized to distribute medicines", value=False)
            submitted = st.form_submit_button("Register NGO", type="primary", use_container_width=True)

        if submitted:
            if not verified:
                st.error("Please confirm authorization.")
                return
            data = {
                "name": name, "email": email, "phone": phone, "city": city,
                "locality": locality, "medicines": medicines, "pincode": pincode,
                "category_preferences": prefs,
            }
            model, err = validate_ngo(data)
            if err:
                st.error(err)
                return
            with st.spinner("Registering…"):
                ngo_id = ngo_repo.create_ngo({
                    "name": model.name,
                    "email": str(model.email),
                    "phone": model.phone,
                    "city": model.city,
                    "locality": model.locality,
                    "medicines": model.medicines,
                    "pincode": model.pincode,
                    "category_preferences": model.category_preferences,
                })
                ngo = ngo_repo.get_ngo(ngo_id)
                matches = find_matches_for_ngo(ngo)
                notify(str(model.email), "NGO registered", f"Found {len(matches)} nearby donor(s).", "success")
            st.session_state.user_role = "ngo"
            st.session_state.ngo_profile = {"id": ngo_id, "name": model.name, "email": str(model.email)}
            st.success("NGO registered! Open **NGO dashboard** to manage donations.")
            st.toast("Registration complete", icon="✅")

    with tab_dash:
        ngos = ngo_repo.get_all_ngos()
        if not ngos:
            empty_state("🏢", "No NGO registered", "Complete registration first.")
            return

        opts = {f"{n['name']} ({n['city']})": n for n in ngos}
        sel = st.selectbox("Select NGO", list(opts.keys()))
        ngo = opts[sel]
        st.session_state.ngo_profile = {"id": ngo["id"], "name": ngo["name"], "email": ngo["email"]}

        incoming, inventory, delivery, analytics = st.tabs(
            ["Incoming donations", "Inventory", "Delivery tracking", "Analytics"]
        )

        matches = find_matches_for_ngo(ngo, min_score=40)

        with incoming:
            if not matches:
                empty_state("📭", "No incoming donations", "Lower match threshold or wait for new donors.")
            for m in matches:
                d = m["donor"]
                with st.container(border=True):
                    st.markdown(f"**{d['name']}** — {d['medicine']} ({d.get('quantity', 1)} units)")
                    st.caption(f"{d['locality']}, {d['city']}")
                    st.markdown(confidence_badge(m["confidence_score"], m["match_type"]), unsafe_allow_html=True)
                    a1, a2, a3 = st.columns(3)
                    all_m = match_repo.get_matches_with_details()
                    row = next(
                        (x for x in all_m if x.get("donor_id") == d["id"] and x.get("ngo_id") == ngo["id"]),
                        None,
                    )
                    if row:
                        if a1.button("Accept", key=f"acc_{row['id']}"):
                            claim_donation(row["id"])
                            notify(d.get("email", ""), "Donation accepted", f"NGO {ngo['name']} accepted your donation.", "info")
                            st.toast("Accepted", icon="✅")
                            st.rerun()
                        if a2.button("Schedule pickup", key=f"pick_{row['id']}"):
                            update_donation_status(row["id"], "picked_up")
                            st.rerun()
                        if a3.button("Reject", key=f"rej_{row['id']}"):
                            match_repo.delete_match(row["id"])
                            st.rerun()

        with inventory:
            rows = [{"Medicine": m["donor"]["medicine"], "Qty": m["donor"].get("quantity", 1),
                     "Status": m["donor"].get("status", "available")} for m in matches]
            st.dataframe(pd.DataFrame(rows) if rows else pd.DataFrame(), use_container_width=True)

        with delivery:
            for m in matches[:5]:
                d = m["donor"]
                st.markdown(f"**{d.get('medicine')}**")
                render_timeline(d.get("status", "available"))

        with analytics:
            city_counts = donor_repo.get_donor_counts_by_city()
            if city_counts:
                st.bar_chart(city_counts)
            type_counts = donor_repo.get_medicine_type_counts()
            if type_counts:
                st.bar_chart(type_counts)
