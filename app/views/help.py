"""Help & FAQ."""

import streamlit as st

from app.ui import render_footer, render_page_header


def render() -> None:
    render_page_header("Help & FAQ", "Quick answers for donors, NGOs, and admins", "❓")

    with st.expander("How do I donate medicine?", expanded=True):
        st.markdown(
            "1. Go to **Donate Medicines**\n"
            "2. Complete the 3-step form (contact → medicine → pickup)\n"
            "3. Review NGO matches and submit\n"
            "4. Track status in **My dashboard**"
        )

    with st.expander("How do NGOs receive donations?"):
        st.markdown(
            "Register under **NGO Portal**. The system fuzzy-matches your city, "
            "locality, and accepted medicines with nearby donors."
        )

    with st.expander("What statuses mean"):
        st.markdown(
            "| Status | Meaning |\n|--------|--------|\n"
            "| Submitted | Donation registered |\n"
            "| Matched | NGO pairing found |\n"
            "| Accepted | NGO claimed |\n"
            "| Picked up | Collected |\n"
            "| Delivered | Completed |"
        )

    with st.expander("Admin access (staff only)"):
        st.markdown(
            "On startup you choose **Admin portal** (separate from the public site). "
            "First visit lets you create an admin account, or use **Quick login** with "
            "`admin` / `admin123` from `.env`."
        )

    with st.expander("Scan medicine labels (OCR)"):
        st.markdown(
            "**Scan & Tools** reads your medicine photo locally (RapidOCR — no cloud fees). "
            "It suggests name, batch, dates, and quantity. Always verify before submitting. "
            "You can also scan from **Donate → Step 2**."
        )

    with st.expander("Live nearby map (free GPS)"):
        st.markdown(
            "On **Map → Live nearby**, allow browser location or enter a pincode. "
            "We show real pharmacies/clinics from **OpenStreetMap** plus donations and NGOs "
            "in this app near you. No paid map API required."
        )

    with st.expander("Tracking QR & receipt"):
        st.markdown(
            "After donating you get a **tracking ID**, optional **QR code**, and a "
            "**downloadable text receipt** for your records."
        )

    with st.expander("Is this free?"):
        st.markdown(
            "Yes — Streamlit + SQLite + free OCR/maps/charts. "
            "First OCR use may download a small on-device model (~10MB)."
        )

    st.markdown("### Need help?")
    st.info("Demo support: support@meddonate.demo · Emergency: 108 / 102")
    render_footer()
