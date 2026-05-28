"""In-app notification center."""

import streamlit as st

from app.repositories.notification_repo import get_for_recipient, mark_all_read, mark_read
from app.ui import empty_state, render_breadcrumb, render_page_header


def render() -> None:
    render_page_header("Notifications", "Updates on matches, pickups, and deliveries", "🔔")
    render_breadcrumb("Home", "Notifications")

    email = st.session_state.get("donor_profile", {}).get("email")
    if not email:
        st.info("Register or donate as a donor to receive personal notifications.")
        email = st.text_input("View notifications for email", placeholder="your@email.com")
        if not email:
            empty_state("🔔", "No inbox yet", "Enter your email or complete a donation first.")
            return

    items = get_for_recipient(email)
    if not items:
        empty_state(
            "📭",
            "No notifications yet",
            "You'll see updates when NGOs match or status changes.",
        )
        return

    if st.button("Mark all as read"):
        mark_all_read(email)
        st.rerun()

    for n in items:
        read = n.get("is_read", 0)
        with st.container(border=True):
            st.markdown(f"**{n.get('title')}** {'· ✓ read' if read else '· 🆕 new'}")
            st.caption(n.get("created_at", ""))
            st.write(n.get("body", ""))
            if not read:
                if st.button("Mark read", key=f"read_{n['id']}"):
                    mark_read(n["id"])
                    st.rerun()
