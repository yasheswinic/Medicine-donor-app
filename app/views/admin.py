"""Admin — reliable login (no st.form) + control center."""

import pandas as pd
import streamlit as st

from app.config import settings
from app.repositories import donor_repo, match_repo, ngo_repo
from app.services.auth_service import admin_exists, create_admin, reset_admin_to_env, verify_admin
from app.ui import confirm_action, empty_state, render_admin_banner, render_page_header


def _logout() -> None:
    st.session_state.admin_logged_in = False
    st.session_state.pop("admin_user", None)
    st.session_state.pop("login_error", None)


def _attempt_login(username: str, password: str) -> bool:
    """Returns True if login succeeded."""
    from app.ui import enter_admin_portal

    enter_admin_portal()
    if not username.strip() or not password:
        st.session_state.login_error = "Enter both username and password."
        return False
    if verify_admin(username, password):
        st.session_state.admin_logged_in = True
        st.session_state.admin_user = username.strip().lower()
        st.session_state.login_error = None
        return True
    st.session_state.login_error = "Invalid username or password. Try again."
    return False


def render_login_or_setup() -> None:
    render_page_header("Admin Portal", "Staff access — separate from the public site", "🔐")
    render_admin_banner()

    _, center, _ = st.columns([1, 2, 1])
    with center:
        if not admin_exists():
            st.info("**First time here?** Create your admin account below.")
            with st.container(border=True):
                u = st.text_input("Choose username", value="admin", key="setup_user")
                p1 = st.text_input("Password (min 6 chars)", type="password", key="setup_p1")
                p2 = st.text_input("Confirm password", type="password", key="setup_p2")
                if st.button("Create admin account", type="primary", use_container_width=True):
                    if len(p1) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif p1 != p2:
                        st.error("Passwords do not match.")
                    else:
                        create_admin(u, p1)
                        from app.ui import enter_admin_portal
                        enter_admin_portal()
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_user = u.strip().lower()
                        st.toast("Account created — you are logged in!", icon="✅")
                        st.rerun()
            return

        with st.container(border=True):
            st.markdown("### Sign in to Admin")
            if st.session_state.get("login_error"):
                st.error(st.session_state.login_error)

            username = st.text_input("Username", key="admin_username")
            password = st.text_input("Password", type="password", key="admin_password")

            if st.button("Log in", type="primary", use_container_width=True, key="btn_admin_login"):
                with st.spinner("Signing in…"):
                    if _attempt_login(username, password):
                        st.toast("Welcome back!", icon="✅")
                st.rerun()

            st.markdown("---")
            if st.button(
                "Quick login (admin / admin123)",
                use_container_width=True,
                key="btn_demo_login",
            ):
                with st.spinner("Signing in…"):
                    if _attempt_login(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD):
                        st.toast("Logged in with demo account", icon="✅")
                st.rerun()

            with st.expander("Trouble signing in?"):
                st.markdown(
                    "Default from `.env`: **admin** / **admin123**  \n"
                    "If you forgot your password, reset to defaults:"
                )
                if st.button("Reset admin to admin / admin123", key="reset_admin"):
                    reset_admin_to_env(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
                    st.success("Reset done. Click **Quick login** above.")
                    st.rerun()


def render_dashboard() -> None:
    render_page_header(
        "Admin Console",
        f"Signed in as {st.session_state.get('admin_user', 'admin')}",
        "🔐",
    )
    if st.button("Log out", type="secondary"):
        _logout()
        st.rerun()

    total_d = donor_repo.count_donors()
    total_n = ngo_repo.count_ngos()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Donations", total_d)
    c2.metric("NGOs", total_n)
    c3.metric("Pending matches", match_repo.count_by_status("pending"))
    c4.metric("Completed", match_repo.count_by_status("completed"))

    tab_over, tab_d, tab_n, tab_m, tab_export = st.tabs(
        ["Overview", "Donors", "NGOs", "Matches", "Export"]
    )

    with tab_over:
        st.markdown("#### Pipeline")
        for status in ("available", "pending", "claimed", "picked_up", "completed"):
            n = donor_repo.count_by_status(status)
            st.progress(min(1.0, n / max(total_d, 1)), text=f"{status}: {n}")

    with tab_d:
        donors = donor_repo.get_all_donors()
        if donors:
            st.dataframe(pd.DataFrame(donors), use_container_width=True, hide_index=True)
        else:
            empty_state("👤", "No donors yet", "")

    with tab_n:
        ngos = ngo_repo.get_all_ngos()
        if ngos:
            st.dataframe(pd.DataFrame(ngos), use_container_width=True, hide_index=True)
        else:
            empty_state("🏢", "No NGOs yet", "")

    with tab_m:
        matches = match_repo.get_matches_with_details()
        if matches:
            st.dataframe(pd.DataFrame(matches), use_container_width=True, hide_index=True)
        else:
            empty_state("🔗", "No matches — run matching from Dashboard", "")

    with tab_export:
        donors = donor_repo.get_all_donors()
        ngos = ngo_repo.get_all_ngos()
        matches = match_repo.get_matches_with_details()
        c1, c2, c3 = st.columns(3)
        if donors:
            c1.download_button("Donors CSV", pd.DataFrame(donors).to_csv(index=False), "donors.csv")
        if ngos:
            c2.download_button("NGOs CSV", pd.DataFrame(ngos).to_csv(index=False), "ngos.csv")
        if matches:
            c3.download_button("Matches CSV", pd.DataFrame(matches).to_csv(index=False), "matches.csv")


def render() -> None:
    if st.session_state.get("admin_logged_in"):
        render_dashboard()
    else:
        render_login_or_setup()
