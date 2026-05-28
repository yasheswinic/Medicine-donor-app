"""Shared UI — separate Public vs Admin portals."""

import streamlit as st

from app.constants import ASSETS_DIR

# Public navigation only (no admin mixed in)
NAV_MAIN = [
    "🏠 Home",
    "💊 Donate Medicines",
    "🔬 Scan & Tools",
    "🏢 NGO Portal",
    "📊 Dashboard",
    "🗺️ Map",
    "🔔 Notifications",
    "❓ Help & FAQ",
]

DONATION_TIMELINE = [
    ("available", "Submitted"),
    ("pending", "Matched"),
    ("claimed", "Accepted"),
    ("picked_up", "Picked up"),
    ("completed", "Delivered"),
]

STATUS_PILL = {
    "available": ("🟢", "#dcfce7", "#166534"),
    "pending": ("🟡", "#fef9c3", "#854d0e"),
    "claimed": ("🟡", "#fef9c3", "#854d0e"),
    "picked_up": ("🔵", "#dbeafe", "#1e40af"),
    "completed": ("✅", "#dcfce7", "#166534"),
    "expired": ("🔴", "#fee2e2", "#991b1b"),
}


def init_session() -> None:
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "app_portal" not in st.session_state:
        st.session_state.app_portal = None
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = NAV_MAIN[0]
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "donor_profile" not in st.session_state:
        st.session_state.donor_profile = {}
    if "ngo_profile" not in st.session_state:
        st.session_state.ngo_profile = {}
    if "donor_draft" not in st.session_state:
        st.session_state.donor_draft = {}
    if "donor_step" not in st.session_state:
        st.session_state.donor_step = 0
    if "login_error" not in st.session_state:
        st.session_state.login_error = None
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    if "user_location" not in st.session_state:
        st.session_state.user_location = None


def enter_public_portal() -> None:
    st.session_state.app_portal = "public"
    st.session_state.nav_page = NAV_MAIN[0]
    st.session_state.admin_logged_in = False
    st.session_state.pop("admin_user", None)


def enter_admin_portal() -> None:
    st.session_state.app_portal = "admin"
    st.session_state.admin_logged_in = False
    st.session_state.pop("admin_user", None)
    st.session_state.login_error = None


def exit_to_portal_selector() -> None:
    st.session_state.app_portal = None
    st.session_state.admin_logged_in = False
    st.session_state.pop("admin_user", None)
    st.session_state.login_error = None


def set_nav(page: str) -> None:
    if page in NAV_MAIN and st.session_state.get("app_portal") == "public":
        st.session_state.nav_page = page


def load_css() -> None:
    css_path = ASSETS_DIR / "styles.css"
    base = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    dark = st.session_state.get("theme") == "dark"
    theme_vars = """
    :root {
        --app-bg: #0f172a; --sidebar-bg: #1e293b; --content-bg: #1e293b;
        --text: #f1f5f9; --hero-from: #1e3a5f; --hero-to: #2563eb;
    }
    """ if dark else """
    :root {
        --app-bg: #eef6f9; --sidebar-bg: #ffffff; --content-bg: #ffffff;
        --text: #0f172a; --hero-from: #0d9488; --hero-to: #1565c0;
    }
    """
    st.markdown(f"<style>{theme_vars}{base}</style>", unsafe_allow_html=True)


def render_portal_sidebar_hint() -> None:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="logo">🩺</div>
            <div class="title">MedDonate</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Select a portal on the right →")


def render_public_sidebar() -> None:
    unread = 0
    if st.session_state.get("donor_profile", {}).get("email"):
        from app.repositories.notification_repo import get_unread_count
        unread = get_unread_count(st.session_state.donor_profile["email"])

    st.markdown(
        """
        <div class="sidebar-brand public-brand">
            <div class="logo">🩺</div>
            <div class="title">MedDonate</div>
            <div class="tagline">Public · Donors & NGOs</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("user_role") == "donor":
        st.success(f"👤 {st.session_state.donor_profile.get('name', 'Donor')}")
    elif st.session_state.get("user_role") == "ngo":
        st.success(f"🏢 {st.session_state.ngo_profile.get('name', 'NGO')}")

    st.markdown("**Menu**")
    nav_labels = list(NAV_MAIN)
    notif_idx = NAV_MAIN.index("🔔 Notifications")
    if unread:
        nav_labels[notif_idx] = f"🔔 Notifications ({unread})"

    current = st.session_state.nav_page
    idx = next((i for i, l in enumerate(NAV_MAIN) if current == l), 0)
    if "Notifications" in current:
        idx = notif_idx

    choice = st.radio("nav", nav_labels, index=idx, label_visibility="collapsed", key="public_nav")
    cleaned = choice.split(" (")[0] if " (" in choice else choice
    for label in NAV_MAIN:
        if cleaned == label:
            st.session_state.nav_page = label
            break

    st.markdown("---")
    theme = st.toggle("🌙 Dark mode", value=st.session_state.theme == "dark")
    st.session_state.theme = "dark" if theme else "light"

    if st.session_state.get("user_role"):
        if st.button("🚪 Sign out", use_container_width=True):
            st.session_state.user_role = None
            st.session_state.donor_profile = {}
            st.session_state.ngo_profile = {}
            st.toast("Signed out")
            st.rerun()

    with st.expander("🔍 Search"):
        gq = st.text_input("Search", label_visibility="collapsed", key="pub_search")
        if gq:
            render_global_search_results(gq)

    st.markdown("---")
    if st.button("↩ Switch portal", use_container_width=True):
        exit_to_portal_selector()
        st.rerun()

    st.caption("Public site · Not admin")


def render_admin_sidebar() -> None:
    st.markdown(
        """
        <div class="sidebar-brand admin-brand">
            <div class="logo">🔐</div>
            <div class="title">MedDonate Admin</div>
            <div class="tagline">Staff portal only</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("admin_logged_in"):
        st.success(f"Staff: **{st.session_state.get('admin_user', 'admin')}**")
    else:
        st.warning("Not signed in")

    st.markdown("---")
    theme = st.toggle("🌙 Dark mode", value=st.session_state.theme == "dark", key="admin_theme")
    st.session_state.theme = "dark" if theme else "light"

    if st.session_state.get("admin_logged_in"):
        if st.button("🚪 Admin sign out", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.session_state.pop("admin_user", None)
            st.session_state.login_error = None
            st.toast("Signed out")
            st.rerun()

    st.markdown("---")
    if st.button("↩ Switch portal", use_container_width=True, key="admin_switch"):
        exit_to_portal_selector()
        st.rerun()

    st.caption("Admin · Separate from public site")


def render_hero_landing() -> None:
    st.markdown(
        """
        <div class="landing-hero">
            <div class="landing-logo">🩺</div>
            <h1>MedDonate</h1>
            <p class="landing-tagline">Connecting Medicine Donors with NGOs</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_steps() -> None:
    c1, c2, c3 = st.columns(3)
    steps = [
        ("1", "💊", "Donors list medicines", "Upload details, photos, and expiry info."),
        ("2", "🏢", "NGOs get matched", "Nearby NGOs see compatible donations."),
        ("3", "❤️", "Medicines reach people", "Track pickup through delivery."),
    ]
    for col, (num, icon, title, desc) in zip([c1, c2, c3], steps):
        with col:
            st.markdown(
                f'<div class="step-card"><span class="step-num">{num}</span>'
                f'<div class="step-icon">{icon}</div><h4>{title}</h4><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )


def render_page_header(title: str, subtitle: str = "", icon: str = "💊") -> None:
    st.markdown(
        f'<div class="page-header"><h1>{icon} {title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def render_admin_banner() -> None:
    st.markdown(
        '<div class="admin-banner">🔐 <b>Admin portal</b> — staff only. '
        "This area is separate from the public donor/NGO site.</div>",
        unsafe_allow_html=True,
    )


def render_breadcrumb(*parts: str) -> None:
    st.caption(" › ".join(parts))


def render_timeline(current_status: str) -> None:
    statuses = [s[0] for s in DONATION_TIMELINE]
    try:
        idx = statuses.index(current_status)
    except ValueError:
        idx = 0
    cols = st.columns(len(DONATION_TIMELINE))
    for i, (code, label) in enumerate(DONATION_TIMELINE):
        done = i <= idx
        color = "#1565c0" if done else "#cbd5e1"
        with cols[i]:
            st.markdown(
                f'<div style="text-align:center;">'
                f'<div style="width:28px;height:28px;border-radius:50%;background:{color};'
                f'margin:0 auto;color:white;font-size:12px;line-height:28px;">'
                f'{"✓" if done else i+1}</div>'
                f'<div style="font-size:11px;margin-top:4px;font-weight:600;">{label}</div></div>',
                unsafe_allow_html=True,
            )


def donor_status_pill(status: str) -> str:
    emoji, bg, fg = STATUS_PILL.get(status, ("⚪", "#f1f5f9", "#475569"))
    return (
        f'<span class="status-pill" style="background:{bg};color:{fg};">'
        f"{emoji} {status.replace('_', ' ').title()}</span>"
    )


def status_badge(status: str) -> str:
    return donor_status_pill(status)


def confidence_badge(score: float, match_type: str) -> str:
    colors = {"exact_match": "#16a34a", "partial_match": "#ca8a04", "low_confidence_match": "#dc2626"}
    color = colors.get(match_type, "#64748b")
    return f'<span class="badge" style="background:{color};">{score:.0f}% · {match_type.replace("_", " ").title()}</span>'


def empty_state(icon: str, title: str, message: str, action_label: str = "", action_page: str = "") -> None:
    st.markdown(
        f'<div class="glass-card empty-state"><div class="empty-icon">{icon}</div>'
        f"<h3>{title}</h3><p>{message}</p></div>",
        unsafe_allow_html=True,
    )
    if action_label and action_page:
        if st.button(action_label, use_container_width=True):
            set_nav(action_page)
            st.rerun()


def render_global_search_results(query: str) -> None:
    from app.services.search_service import global_search

    if len(query.strip()) < 2:
        return
    with st.spinner("Searching…"):
        results = global_search(query)
    total = sum(len(v) for v in results.values())
    if not total:
        st.info("No results.")
        return
    st.success(f"{total} found")
    for d in results["donors"][:3]:
        st.caption(f"💊 {d.get('medicine')} · {d.get('city')}")
    for n in results["ngos"][:3]:
        st.caption(f"🏢 {n.get('name')}")


def confirm_action(message: str, key: str) -> bool:
    st.warning(message)
    return st.button("Yes, continue", key=f"{key}_yes", use_container_width=True)


def render_footer() -> None:
    st.markdown("---")
    f1, f2, f3 = st.columns(3)
    f1.caption("**About** · Medicine donation platform")
    f2.caption("**Contact** · support@meddonate.demo")
    f3.caption("**Emergency** · 108 / 102")
