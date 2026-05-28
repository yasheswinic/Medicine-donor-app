"""MedDonate — public portal + separate admin portal."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.ui import (
    NAV_MAIN,
    init_session,
    load_css,
    render_admin_sidebar,
    render_portal_sidebar_hint,
    render_public_sidebar,
)
from app.utils import setup_logging

setup_logging()
init_session()

st.set_page_config(
    page_title="MedDonate",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from app.db import init_db

    init_db()
except Exception as e:
    st.error("Database could not start.")
    st.code(str(e))
    st.stop()

from app.views import admin, dashboard, donor, help, home, map_view, ngo, notifications, portal, tools

PUBLIC_PAGES = {
    "🏠 Home": home,
    "💊 Donate Medicines": donor,
    "🔬 Scan & Tools": tools,
    "🏢 NGO Portal": ngo,
    "📊 Dashboard": dashboard,
    "🗺️ Map": map_view,
    "🔔 Notifications": notifications,
    "❓ Help & FAQ": help,
}

load_css()

portal_mode = st.session_state.get("app_portal")

# ─── Step 1: Portal chooser (no mixed navigation) ───
if portal_mode is None:
    with st.sidebar:
        render_portal_sidebar_hint()
    portal.render()
    st.stop()

# ─── Step 2: Admin portal (completely separate) ───
if portal_mode == "admin":
    with st.sidebar:
        render_admin_sidebar()
    try:
        admin.render()
    except Exception as e:
        st.error("Admin portal error.")
        with st.expander("Details"):
            st.exception(e)
    st.stop()

# ─── Step 3: Public portal (donors & NGOs only) ───
with st.sidebar:
    render_public_sidebar()

page = st.session_state.nav_page
if page not in PUBLIC_PAGES:
    st.session_state.nav_page = NAV_MAIN[0]
    st.rerun()

try:
    PUBLIC_PAGES[page].render()
except Exception as e:
    st.error("Something went wrong.")
    with st.expander("Details"):
        st.exception(e)
