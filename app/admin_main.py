"""Optional entry: admin portal only.

Run: streamlit run app/admin_main.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.ui import enter_admin_portal, init_session, load_css, render_admin_sidebar
from app.utils import setup_logging

setup_logging()
init_session()
enter_admin_portal()

st.set_page_config(page_title="MedDonate Admin", page_icon="🔐", layout="wide")

from app.db import init_db

init_db()
load_css()

from app.views import admin

with st.sidebar:
    render_admin_sidebar()

admin.render()
