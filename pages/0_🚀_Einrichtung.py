import streamlit as st
import urllib.parse
import http.server
import requests as req
from src import config as cfg

cfg.apply_to_env()


c = cfg.load()

if c.get("setup_complete"):
    st.success("✅ Einrichtung bereits abgeschlossen.")
    st.caption("Einstellungen ändern → ⚙️ Einstellungen")
    st.stop()

# ── Step state ────────────────────────────────────────────────────────────────

if "setup_step" not in st.session_state:
    st.session_state.setup_step = 1

TOTAL_STEPS = 5

def next_step():
    st.session_state.setup_step += 1

def prev_step():
    st.session_state.setup_step -= 1

step = st.session_state.setup_step

# ── Header ────────────────────────────────────────────────────────────────────

st.title("🚀 Einrichtung")
st.progress(step / TOTAL_STEPS, text=f"Schritt {step} von {TOTAL_STEPS}")
st.divider()

# ── Step 1: Willkommen ────────────────────────────────────────────────────────

if step == 1:
    st.header("Willkommen!")
    st.markdown("""
Dieser Assistent führt dich in **5 Schritten** durch die Einrichtung:

1. **Business-Profil** — wer du bist, was du anbietest
2. **OpenAI Key** — für die Content-Generierung
3. **LinkedIn verbinden** — für automatisches Posten
4. **Post-Einstellungen** — Länge, Ton, Frequenz
5. **Fertig** — los geht's!

Die Einrichtung dauert ca. **10 Minuten**.
    """)
    st.info("Tipp: Du kannst jederzeit in ⚙️ Einstellungen Änderungen vornehmen.")
    if st.button("Los geht's →", type="primary", use_container_width=True):
        next_step()
        st.rerun()

# ── Step 2: Business-Profil ───────────────────────────────────────────────────

elif step == 2:
    st.header("Schritt 1: Business-Profil")
    st.caption("Diese Angaben bestimmen, wie der AI-Agent in deiner Stimme schreibt.")

    name = st.text_input("Dein Name oder Unternehmensname *",
                          value=c.get("business_name", ""),
                          placeholder="z.B. Wolfgang Heis")
    description = st.text_area(
        "Was du anbietest *",
        value=c.get("business_description", ""),
        height=120,
        placeholder="z.B. Ich bin Webdesigner in Wien und helfe kleinen Unternehmen zu einem professionellen Auftritt im Netz …",
    )
    target = st.text_input("Deine Zielgruppe",
                            value=c.get("business_target", ""),
                            placeholder="z.B. Selbstständige und KMU in Österreich")
    tone = st.text_area(
        "Deine Stimme / Tonalität",
        value=c.get("business_tone_hints", ""),
        height=80,
        placeholder="z.B. direkt, ehrlich, auf Augenhöhe, keine Buzzwords",
    )
    language = st.selectbox(
        "Sprache der Posts",
        ["Deutsch", "Englisch", "Französisch", "Spanisch", "Italienisch"],
        index=["Deutsch", "Englisch", "Französisch", "Spanisch", "Italienisch"].index(
            c.get("business_language", "Deutsch")),
    )

    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← Zurück", use_container_width=True):
            prev_step()
            st.rerun()
    with col_next:
        if st.button("Weiter →", type="primary", use_container_width=True):
            if not name or not description:
                st.error("Bitte Name und Beschreibung ausfüllen.")
            else:
                c.update({
                    "business_name": name,
                    "business_description": description,
                    "business_target": target,
                    "business_tone_hints": tone,
                    "business_language": language,
                })
                cfg.save(c)
                next_step()
                st.rerun()

# ── Step 3: OpenAI Key ────────────────────────────────────────────────────────

elif step == 3:
    st.header("Schritt 2: OpenAI API Key")
    st.markdown("""
Der Key wird benötigt, um deine Posts mit GPT-4o zu generieren.

**Key holen:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys) → *Create new secret key*
    """)

    openai_key = st.text_input("OpenAI API Key *",
                                 value=c.get("openai_api_key", ""),
                                 type="password",
                                 placeholder="sk-proj-…")

    if openai_key and not openai_key.startswith("sk-"):
        st.warning("Key sieht ungewöhnlich aus — beginnt normalerweise mit 'sk-'")

    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← Zurück", use_container_width=True):
            prev_step()
            st.rerun()
    with col_next:
        if st.button("Weiter →", type="primary", use_container_width=True):
            if not openai_key:
                st.error("Bitte OpenAI Key eingeben.")
            else:
                c["openai_api_key"] = openai_key
                cfg.save(c)
                cfg.apply_to_env()
                next_step()
                st.rerun()

# ── Step 4: LinkedIn verbinden ────────────────────────────────────────────────

elif step == 4:
    st.header("Schritt 3: LinkedIn verbinden")

    already_connected = bool(c.get("linkedin_access_token") and c.get("linkedin_author_urn"))
    if already_connected:
        st.success(f"✅ LinkedIn bereits verbunden: `{c.get('linkedin_author_urn')}`")
        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Zurück", use_container_width=True):
                prev_step()
                st.rerun()
        with col_next:
            if st.button("Weiter →", type="primary", use_container_width=True):
                next_step()
                st.rerun()
        st.stop()

    st.markdown("""
**Voraussetzungen (einmalig, 5 Min):**
1. LinkedIn Developer App erstellen: [linkedin.com/developers](https://www.linkedin.com/developers/apps)
2. Produkte aktivieren: *Share on LinkedIn* + *Sign in with LinkedIn using OpenID Connect*
3. Redirect URI eintragen: `http://localhost:8765/callback`
    """)

    with st.expander("Ich habe bereits eine App — hier eingeben"):
        col1, col2 = st.columns(2)
        with col1:
            li_client_id = st.text_input("Client ID", key="onb_li_cid")
        with col2:
            li_client_secret = st.text_input("Client Secret", type="password", key="onb_li_csecret")

        if st.button("🔗 LinkedIn verbinden", type="primary"):
            if not li_client_id or not li_client_secret:
                st.error("Client ID und Secret eingeben.")
            else:
                scopes = "openid profile w_member_social"
                redirect = "http://localhost:8765/callback"
                auth_url = (
                    f"https://www.linkedin.com/oauth/v2/authorization"
                    f"?response_type=code&client_id={li_client_id}"
                    f"&redirect_uri={urllib.parse.quote(redirect)}"
                    f"&scope={urllib.parse.quote(scopes)}&state=wsa"
                )

                import webbrowser, http.server as _hs
                code_holder = []

                class Handler(_hs.BaseHTTPRequestHandler):
                    def do_GET(self):
                        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                        if "code" in params:
                            code_holder.append(params["code"][0])
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"<h2>Fertig! Diesen Tab schliessen.</h2>")
                    def log_message(self, *a): pass

                server = _hs.HTTPServer(("localhost", 8765), Handler)
                webbrowser.open(auth_url)
                with st.spinner("Warte auf Browser-Bestätigung …"):
                    server.handle_request()

                if code_holder:
                    try:
                        tr = req.post("https://www.linkedin.com/oauth/v2/accessToken", data={
                            "grant_type": "authorization_code",
                            "code": code_holder[0],
                            "redirect_uri": redirect,
                            "client_id": li_client_id,
                            "client_secret": li_client_secret,
                        })
                        token = tr.json()["access_token"]
                        ui = req.get("https://api.linkedin.com/v2/userinfo",
                                     headers={"Authorization": f"Bearer {token}"})
                        urn = f"urn:li:person:{ui.json()['sub']}"
                        c["linkedin_access_token"] = token
                        c["linkedin_author_urn"] = urn
                        from datetime import datetime
                        c["linkedin_token_date"] = datetime.now().isoformat()
                        cfg.save(c)
                        cfg.apply_to_env()
                        st.success(f"✅ Verbunden: {urn}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")

    st.divider()
    col_back, col_skip = st.columns([1, 3])
    with col_back:
        if st.button("← Zurück", use_container_width=True):
            prev_step()
            st.rerun()
    with col_skip:
        if st.button("Überspringen (später einrichten) →", use_container_width=True):
            next_step()
            st.rerun()

# ── Step 5: Post-Einstellungen ────────────────────────────────────────────────

elif step == 5:
    st.header("Schritt 4: Post-Einstellungen")
    st.caption("Kannst du jederzeit in ⚙️ Einstellungen anpassen.")

    col1, col2 = st.columns(2)
    with col1:
        post_linkedin = st.checkbox("LinkedIn posten", value=c.get("post_linkedin", True))
        post_instagram = st.checkbox("Instagram posten", value=c.get("post_instagram", False))
        length = st.select_slider("Post-Länge", options=["Kurz", "Mittel", "Lang"],
                                   value=c.get("post_length", "Mittel"))
    with col2:
        tone = st.radio("Ton", ["Direkt", "Sachlich", "Storytelling"],
                        index=["Direkt", "Sachlich", "Storytelling"].index(
                            c.get("post_tone", "Direkt")))
        hashtags = st.select_slider("Hashtag-Anzahl", options=[5, 8, 10, 12, 15],
                                     value=c.get("hashtag_count", 10))
        use_image = st.toggle("Bild mit DALL-E 3 generieren", value=c.get("generate_image", False))

    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← Zurück", use_container_width=True):
            prev_step()
            st.rerun()
    with col_next:
        if st.button("Einrichtung abschließen ✅", type="primary", use_container_width=True):
            c.update({
                "post_linkedin": post_linkedin,
                "post_instagram": post_instagram,
                "post_length": length,
                "post_tone": tone,
                "hashtag_count": hashtags,
                "generate_image": use_image,
                "setup_complete": True,
            })
            cfg.save(c)
            st.balloons()
            st.success("🎉 Einrichtung abgeschlossen! Gehe zu 🏠 Post erstellen.")
            st.session_state.setup_step = 1
