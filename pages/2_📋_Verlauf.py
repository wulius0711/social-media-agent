import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Verlauf", page_icon="📋", layout="wide")
st.title("📋 Verlauf")

log_candidates = [
    Path.home() / "Library" / "Logs" / "WolfgangSocialAgent.log",
    Path(__file__).parent.parent / "logs" / "agent.log",
]

log_content = ""
for p in log_candidates:
    if p.exists():
        lines = p.read_text().splitlines()[-100:]
        log_content = "\n".join(lines)
        break

if log_content:
    st.code(log_content, language=None)
else:
    st.info("Noch keine Einträge.")

if st.button("🔄 Aktualisieren"):
    st.rerun()
