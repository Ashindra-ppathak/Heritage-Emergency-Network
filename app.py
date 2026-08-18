"""
Heritage Emergency Network
"Protect Heritage Before It Is Lost."

Main Streamlit application entry point.
Run with:  streamlit run app.py
"""

import streamlit as st

from utils.database import init_db, db_exists
from ui.styles import inject_css
from ui import pages

st.set_page_config(
    page_title="Heritage Emergency Network",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Initialize database (safe to call every run) --------------------------
init_db()

# --- Inject premium dark theme ---------------------------------------------
st.markdown(inject_css(), unsafe_allow_html=True)

# --- Session state defaults --------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"
if "role" not in st.session_state:
    st.session_state.role = "Citizen"

PAGES = [
    "🏠 Dashboard",
    "📍 Report Heritage",
    "🧠 AI Risk Assessment",
    "🔎 Verification",
    "🚨 Alerts",
    "🏛 Authority Action",
    "📊 Monitoring",
    "🗺 Heritage Risk Map",
    "📈 Analytics",
    "ℹ About",
]

ROLE_ALLOWED_PAGES = {
    "Citizen": {"🏠 Dashboard", "📍 Report Heritage", "🧠 AI Risk Assessment", "🗺 Heritage Risk Map", "📈 Analytics", "ℹ About"},
    "Verifier": {"🏠 Dashboard", "🧠 AI Risk Assessment", "🔎 Verification", "🗺 Heritage Risk Map", "📈 Analytics", "ℹ About"},
    "Authority": {"🏠 Dashboard", "🧠 AI Risk Assessment", "🚨 Alerts", "🏛 Authority Action", "📊 Monitoring", "🗺 Heritage Risk Map", "📈 Analytics", "ℹ About"},
    "Admin": set(PAGES),
}

# --- Sidebar -----------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 8px 0 4px 0;">
            <div style="font-size:34px;">🏛</div>
            <div style="font-weight:800; font-size:15px; letter-spacing:0.5px;">HERITAGE EMERGENCY<br>NETWORK</div>
            <div style="font-size:11px; color:#94A3B8; margin-top:2px;">Protect Heritage Before It Is Lost.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    st.session_state.role = st.selectbox(
        "Simulated Role", ["Citizen", "Verifier", "Authority", "Admin"],
        index=["Citizen", "Verifier", "Authority", "Admin"].index(st.session_state.role),
        help="This is a prototype role simulation — not real authentication.",
    )
    st.caption("🧪 Prototype simulation — not real authentication.")
    st.divider()

    allowed = ROLE_ALLOWED_PAGES.get(st.session_state.role, set(PAGES))
    visible_pages = [p for p in PAGES if p in allowed]
    if st.session_state.page not in visible_pages:
        st.session_state.page = visible_pages[0]

    choice = st.radio("Navigate", visible_pages, index=visible_pages.index(st.session_state.page), label_visibility="collapsed")
    if choice != st.session_state.page:
        st.session_state.page = choice
        st.rerun()

    st.divider()
    demo_mode = st.toggle("🎬 Demo Mode", value=st.session_state.get("demo_mode", False))
    st.session_state.demo_mode = demo_mode

    st.divider()
    st.caption("HEN Prototype • Local-first • SQLite + optional Ollama (Phi-3)")

# --- Main content --------------------------------------------------------------
if st.session_state.demo_mode:
    pages.render_demo_mode()
    st.divider()

page = st.session_state.page

if page == "🏠 Dashboard":
    pages.render_dashboard()
elif page == "📍 Report Heritage":
    pages.render_report_page()
elif page == "🧠 AI Risk Assessment":
    pages.render_case_file_page()
elif page == "🔎 Verification":
    pages.render_verification_page()
elif page == "🚨 Alerts":
    pages.render_alerts_page()
elif page == "🏛 Authority Action":
    pages.render_authority_page()
elif page == "📊 Monitoring":
    pages.render_monitoring_page()
elif page == "🗺 Heritage Risk Map":
    pages.render_map_page()
elif page == "📈 Analytics":
    pages.render_analytics_page()
elif page == "ℹ About":
    pages.render_about_page()
