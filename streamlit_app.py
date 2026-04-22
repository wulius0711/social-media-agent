import streamlit as st
import threading
from pathlib import Path
from src import config as cfg

cfg.apply_to_env()

st.set_page_config(
    page_title="Social Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────────────────────────

for key, default in {
    "linkedin_text": "",
    "instagram_text": "",
    "facebook_text": "",
    "tiktok_text": "",
    "topic": "",
    "last_status": "",
    "generating": False,
    "posting": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────

c = cfg.load()

with st.sidebar:
    st.title("🚀 Social Agent")
    name = c.get("business_name", "")
    st.caption(name if name else "Profil einrichten →")
    st.divider()

    st.subheader("Plattformen")
    post_li = st.checkbox("LinkedIn", value=c.get("post_linkedin", True))
    post_ig = st.checkbox("Instagram", value=c.get("post_instagram", False))
    post_fb = st.checkbox("Facebook", value=False)
    post_tt = st.checkbox("TikTok", value=False)

    st.divider()
    st.subheader("Einstellungen")
    length = st.select_slider("Länge", options=["Kurz", "Mittel", "Lang"],
                               value=c.get("post_length", "Mittel"))
    tone = st.radio("Ton", ["Direkt", "Sachlich", "Storytelling"],
                    index=["Direkt", "Sachlich", "Storytelling"].index(
                        c.get("post_tone", "Direkt")),
                    horizontal=True)
    hashtags = st.select_slider("Hashtags", options=[5, 8, 10, 12, 15],
                                 value=c.get("hashtag_count", 10))
    use_image = st.toggle("Bild generieren (DALL-E 3)", value=c.get("generate_image", False))

    st.divider()
    # Status
    connected = sum([
        bool(c.get("linkedin_access_token")),
        bool(str(c.get("instagram_access_token", "")).startswith("EAA")),
    ])
    st.caption(f"✅ {connected} von 2 Plattformen verbunden")


# ── Main area ─────────────────────────────────────────────────────────────────

st.header("Post erstellen")

col_topic, col_btn = st.columns([4, 1])
with col_topic:
    topic = st.text_input(
        "Thema",
        placeholder="Leer lassen für zufälliges Thema …",
        label_visibility="collapsed",
    )
with col_btn:
    generate = st.button("✨ Vorschau generieren", use_container_width=True, type="primary")

if generate:
    if not c.get("openai_api_key"):
        st.error("OpenAI API Key fehlt — bitte in ⚙️ Einstellungen eintragen.")
    else:
        with st.spinner("Generiere Content …"):
            from src.content_generator import generate_content
            ig, li = generate_content(
                custom_topic=topic or None,
                length=length,
                tone=tone,
                hashtag_count=hashtags,
            )
            st.session_state.linkedin_text   = li["text"]
            st.session_state.instagram_text  = ig["caption"]
            st.session_state.facebook_text   = li["text"]
            st.session_state.tiktok_text     = ig["caption"]
            st.session_state.topic           = ig["topic"]
            st.session_state.last_status     = f"Vorschau bereit · Thema: {ig['topic']}"

st.divider()

# Preview tabs
tab_li, tab_ig, tab_fb, tab_tt = st.tabs(["LinkedIn", "Instagram", "Facebook", "TikTok"])

with tab_li:
    st.session_state.linkedin_text = st.text_area(
        "LinkedIn", value=st.session_state.linkedin_text,
        height=300, label_visibility="collapsed",
        placeholder="Klicke auf 'Vorschau generieren' …"
    )

with tab_ig:
    st.session_state.instagram_text = st.text_area(
        "Instagram", value=st.session_state.instagram_text,
        height=300, label_visibility="collapsed",
        placeholder="Klicke auf 'Vorschau generieren' …"
    )

with tab_fb:
    st.session_state.facebook_text = st.text_area(
        "Facebook", value=st.session_state.facebook_text,
        height=300, label_visibility="collapsed",
        placeholder="Klicke auf 'Vorschau generieren' …"
    )

with tab_tt:
    st.session_state.tiktok_text = st.text_area(
        "TikTok", value=st.session_state.tiktok_text,
        height=300, label_visibility="collapsed",
        placeholder="Klicke auf 'Vorschau generieren' …"
    )

st.divider()

col_status, col_post = st.columns([4, 1])
with col_status:
    if st.session_state.last_status:
        st.caption(st.session_state.last_status)

with col_post:
    has_content = bool(st.session_state.linkedin_text or st.session_state.instagram_text)
    post_btn = st.button("📤 Jetzt posten", use_container_width=True,
                          type="primary", disabled=not has_content)

if post_btn and has_content:
    errors = []
    successes = []
    image_path = None

    with st.spinner("Wird gepostet …"):
        if use_image and st.session_state.topic:
            try:
                from src.image_generator import generate_image
                image_path = generate_image(st.session_state.topic)
            except Exception as e:
                errors.append(f"Bild: {e}")

        if post_li:
            try:
                from src.linkedin_poster import post_to_linkedin
                post_to_linkedin(st.session_state.linkedin_text, image_path)
                successes.append("LinkedIn")
            except Exception as e:
                errors.append(f"LinkedIn: {e}")

        if post_ig:
            import os
            if os.getenv("INSTAGRAM_ACCESS_TOKEN", "").startswith("EAA"):
                try:
                    from src.instagram_poster import post_to_instagram
                    post_to_instagram(st.session_state.instagram_text, image_path)
                    successes.append("Instagram")
                except Exception as e:
                    errors.append(f"Instagram: {e}")
            else:
                errors.append("Instagram: Token fehlt")

        if post_fb:
            errors.append("Facebook: noch nicht eingerichtet")
        if post_tt:
            errors.append("TikTok: noch nicht eingerichtet")

        if image_path:
            import os
            if os.path.exists(image_path):
                os.unlink(image_path)

    if successes:
        st.success(f"✅ Gepostet auf: {', '.join(successes)}")
    if errors:
        st.error("\n".join(errors))
