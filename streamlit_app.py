import hashlib
import streamlit as st
from src import config as cfg

cfg.apply_to_env()

st.set_page_config(
    page_title="Social Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo("assets/logo.svg")

# ── Auth ──────────────────────────────────────────────────────────────────────

def _check_password(pw: str) -> bool:
    stored = st.secrets.get("auth", {}).get("password_hash", "")
    return hashlib.sha256(pw.encode()).hexdigest() == stored

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.title("🔐 Social Agent")
        with st.form("login"):
            pw = st.text_input("Passwort", type="password")
            submitted = st.form_submit_button("Einloggen", use_container_width=True)
        if submitted:
            if _check_password(pw):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Falsches Passwort.")
    st.stop()

# ── Logout in Sidebar ─────────────────────────────────────────────────────────

with st.sidebar:
    name = __import__("src.config", fromlist=["load"]).load().get("business_name", "")
    if name:
        st.caption(name)
    if st.button("🚪 Ausloggen", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ── Navigation ────────────────────────────────────────────────────────────────

pg = st.navigation([
    st.Page("pages/posten.py",              title="Posten",       icon="📝"),
    st.Page("pages/3_✅_Genehmigung.py",    title="Genehmigung",  icon="✅"),
    st.Page("pages/2_📋_Verlauf.py",        title="Verlauf",      icon="📋"),
    st.Page("pages/1_⚙️_Einstellungen.py", title="Einstellungen", icon="⚙️"),
    st.Page("pages/0_🚀_Einrichtung.py",   title="Einrichtung",   icon="🚀"),
    st.Page("pages/4_📖_Handbuch.py",       title="Handbuch",     icon="📖"),
])
pg.run()
