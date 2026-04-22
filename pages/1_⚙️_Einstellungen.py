import streamlit as st
import http.server
import urllib.parse
import webbrowser
import threading
from src import config as cfg

st.set_page_config(page_title="Einstellungen", page_icon="⚙️", layout="wide")
st.title("⚙️ Einstellungen")

c = cfg.load()

# ── Business Profil ───────────────────────────────────────────────────────────

st.subheader("Business-Profil")
st.caption("Diese Angaben fließen direkt in den generierten Content ein.")

col1, col2 = st.columns(2)
with col1:
    business_name = st.text_input("Name / Unternehmensname",
                                   value=c.get("business_name", ""))
    business_target = st.text_input("Zielgruppe",
                                     value=c.get("business_target", ""))
    business_language = st.selectbox(
        "Sprache",
        ["Deutsch", "Englisch", "Französisch", "Spanisch", "Italienisch"],
        index=["Deutsch", "Englisch", "Französisch", "Spanisch", "Italienisch"].index(
            c.get("business_language", "Deutsch"))
    )

with col2:
    business_description = st.text_area(
        "Was du anbietest & Hintergrund",
        value=c.get("business_description", ""),
        height=100,
    )
    business_tone = st.text_area(
        "Deine Stimme / Tonalität",
        value=c.get("business_tone_hints", ""),
        height=100,
        placeholder="z.B. direkt, ehrlich, keine Fachwörter …",
    )

# ── API Keys ──────────────────────────────────────────────────────────────────

st.divider()
st.subheader("API Keys")

col1, col2 = st.columns(2)
with col1:
    openai_key = st.text_input("OpenAI API Key",
                                value=c.get("openai_api_key", ""),
                                type="password",
                                help="platform.openai.com/api-keys")
    imgbb_key = st.text_input("imgbb API Key",
                               value=c.get("imgbb_api_key", ""),
                               type="password",
                               help="api.imgbb.com")
    li_token = st.text_input("LinkedIn Access Token",
                              value=c.get("linkedin_access_token", ""),
                              type="password")
    li_urn = st.text_input("LinkedIn Author URN",
                            value=c.get("linkedin_author_urn", ""),
                            placeholder="urn:li:person:XXXXXXXX")

with col2:
    ig_user_id = st.text_input("Instagram User ID",
                                value=c.get("instagram_user_id", ""))
    ig_token = st.text_input("Instagram Access Token",
                              value=c.get("instagram_access_token", ""),
                              type="password")

st.divider()
st.subheader("Cloudinary (für Video-Posts)")
st.caption("Kostenloser Account reicht. cloudinary.com → Dashboard → Cloud Name / API Key / API Secret")
col1, col2, col3 = st.columns(3)
with col1:
    cloudinary_name = st.text_input("Cloud Name", value=c.get("cloudinary_cloud_name", ""))
with col2:
    cloudinary_key = st.text_input("API Key", value=c.get("cloudinary_api_key", ""))
with col3:
    cloudinary_secret = st.text_input("API Secret", value=c.get("cloudinary_api_secret", ""), type="password")

# ── LinkedIn OAuth ────────────────────────────────────────────────────────────

st.divider()
st.subheader("LinkedIn neu verbinden")
st.caption("Token läuft alle 60 Tage ab — hier erneuern.")

col1, col2, col3 = st.columns(3)
with col1:
    li_client_id = st.text_input("Client ID", key="li_cid")
with col2:
    li_client_secret = st.text_input("Client Secret", type="password", key="li_csecret")
with col3:
    redirect_uri = st.text_input("Redirect URI",
                                  value="http://localhost:8501",
                                  help="Deine Streamlit App URL")

if st.button("🔗 LinkedIn verbinden"):
    if not li_client_id or not li_client_secret:
        st.error("Client ID und Secret eingeben.")
    else:
        redirect = f"{redirect_uri.rstrip('/')}/callback" if "localhost" in redirect_uri else redirect_uri
        scopes = "openid profile w_member_social"
        auth_url = (
            f"https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code&client_id={li_client_id}"
            f"&redirect_uri={urllib.parse.quote(redirect)}"
            f"&scope={urllib.parse.quote(scopes)}&state=wsa"
        )

        if "localhost" in redirect_uri:
            code_holder = []

            class Handler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                    if "code" in params:
                        code_holder.append(params["code"][0])
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"<h2>Fertig! Diesen Tab schliessen.</h2>")
                def log_message(self, *a): pass

            server = http.server.HTTPServer(("localhost", 8765), Handler)
            webbrowser.open(auth_url.replace(redirect, "http://localhost:8765/callback").replace(
                urllib.parse.quote(redirect), urllib.parse.quote("http://localhost:8765/callback")
            ))
            with st.spinner("Warte auf Browser-Bestätigung …"):
                server.handle_request()

            if code_holder:
                import requests as req
                try:
                    tr = req.post("https://www.linkedin.com/oauth/v2/accessToken", data={
                        "grant_type": "authorization_code",
                        "code": code_holder[0],
                        "redirect_uri": "http://localhost:8765/callback",
                        "client_id": li_client_id,
                        "client_secret": li_client_secret,
                    })
                    token = tr.json()["access_token"]
                    ui = req.get("https://api.linkedin.com/v2/userinfo",
                                 headers={"Authorization": f"Bearer {token}"})
                    urn = f"urn:li:person:{ui.json()['sub']}"
                    c["linkedin_access_token"] = token
                    c["linkedin_author_urn"] = urn
                    cfg.save(c)
                    cfg.apply_to_env()
                    st.success(f"✅ Verbunden: {urn}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {e}")
        else:
            st.info(f"Öffne diesen Link und bestätige: [LinkedIn Auth]({auth_url})")

# ── Speichern ─────────────────────────────────────────────────────────────────

st.divider()
if st.button("💾 Einstellungen speichern", type="primary"):
    c.update({
        "business_name": business_name,
        "business_description": business_description,
        "business_target": business_target,
        "business_tone_hints": business_tone,
        "business_language": business_language,
        "openai_api_key": openai_key,
        "imgbb_api_key": imgbb_key,
        "linkedin_access_token": li_token,
        "linkedin_author_urn": li_urn,
        "instagram_user_id": ig_user_id,
        "instagram_access_token": ig_token,
        "cloudinary_cloud_name": cloudinary_name,
        "cloudinary_api_key": cloudinary_key,
        "cloudinary_api_secret": cloudinary_secret,
    })
    cfg.save(c)
    cfg.apply_to_env()
    st.success("✅ Gespeichert!")
