"""Choose between Public site (donors/NGOs) and Admin portal."""

import streamlit as st


def render() -> None:
    st.markdown(
        """
        <div class="portal-hero">
            <div style="font-size:3rem;">🩺</div>
            <h1>Welcome to MedDonate</h1>
            <p>Choose how you want to use the platform</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown(
            """
            <div class="portal-card public">
                <div class="portal-icon">👥</div>
                <h2>Public site</h2>
                <p>For donors and NGOs</p>
                <ul>
                    <li>Donate medicines</li>
                    <li>Register your NGO</li>
                    <li>View matches & map</li>
                    <li>Track donation status</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Enter public site →", type="primary", use_container_width=True, key="enter_public"):
            from app.ui import enter_public_portal
            enter_public_portal()
            st.rerun()

    with c2:
        st.markdown(
            """
            <div class="portal-card admin">
                <div class="portal-icon">🔐</div>
                <h2>Admin portal</h2>
                <p>For staff only</p>
                <ul>
                    <li>Manage donors & NGOs</li>
                    <li>Monitor matches</li>
                    <li>Export reports</li>
                    <li>Not for public users</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Enter admin portal →", use_container_width=True, key="enter_admin"):
            from app.ui import enter_admin_portal
            enter_admin_portal()
            st.rerun()

    st.info("Donors and NGOs should use **Public site**. Only authorized staff use **Admin portal**.")
