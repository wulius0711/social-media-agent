import streamlit as st
import os
from pathlib import Path
from src import config as cfg
from src.post_store import LIMITS, add_pending

cfg.apply_to_env()

st.set_page_config(
    page_title="Social Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state ─────────────────────────────────────────────────────────────

for key, default in {
    "linkedin_text": "",
    "instagram_text": "",
    "facebook_text": "",
    "tiktok_text": "",
    "topic": "",
    "generated": False,
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
    use_image = st.toggle("Bild (DALL-E 3)", value=c.get("generate_image", False))

    st.divider()
    connected = sum([
        bool(c.get("linkedin_access_token")),
        bool(str(c.get("instagram_access_token", "")).startswith("EAA")),
    ])
    pending_count = len([p for p in __import__("src.post_store", fromlist=["get_pending"]).get_pending()])
    st.caption(f"✅ {connected} von 2 Plattformen verbunden")
    if pending_count:
        st.warning(f"⏳ {pending_count} Post{'s' if pending_count > 1 else ''} wartet auf Genehmigung")

    # Token-Ablauf-Warnung
    from datetime import datetime, timedelta
    token_date_str = c.get("linkedin_token_date", "")
    if token_date_str:
        try:
            token_date = datetime.fromisoformat(token_date_str)
            days_left = (token_date + timedelta(days=60) - datetime.now()).days
            if days_left <= 14:
                st.warning(f"⚠️ LinkedIn Token läuft in {days_left} Tagen ab")
        except Exception:
            pass

# ── Main ──────────────────────────────────────────────────────────────────────

if not c.get("setup_complete"):
    st.warning("⚠️ Einrichtung noch nicht abgeschlossen — gehe zu **🚀 Einrichtung** in der Sidebar.")
    st.stop()

st.header("Post erstellen")

col_topic, col_btn = st.columns([4, 1])
with col_topic:
    topic = st.text_input("Thema", placeholder="Leer lassen für zufälliges Thema …",
                           label_visibility="collapsed")
with col_btn:
    generate = st.button("✨ Generieren", use_container_width=True, type="primary")

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
            st.session_state.linkedin_text  = li["text"]
            st.session_state.instagram_text = ig["caption"]
            st.session_state.facebook_text  = li["text"]
            st.session_state.tiktok_text    = ig["caption"]
            st.session_state.topic          = ig["topic"]
            st.session_state.generated      = True
        st.success(f"Thema: **{ig['topic']}**")

st.divider()

# ── Preview tabs mit Zeichenzahl ──────────────────────────────────────────────

def _char_indicator(text: str, limit: int):
    count = len(text)
    pct = count / limit
    color = "🟢" if pct < 0.8 else ("🟡" if pct < 1.0 else "🔴")
    return f"{color} {count:,} / {limit:,} Zeichen"

tab_li, tab_ig, tab_fb, tab_tt = st.tabs(["LinkedIn", "Instagram", "Facebook", "TikTok"])

with tab_li:
    st.caption(_char_indicator(st.session_state.linkedin_text, LIMITS["linkedin"]))
    st.session_state.linkedin_text = st.text_area(
        "LinkedIn", value=st.session_state.linkedin_text, height=280,
        label_visibility="collapsed", placeholder="Klicke auf 'Generieren' …"
    )

with tab_ig:
    st.caption(_char_indicator(st.session_state.instagram_text, LIMITS["instagram"]))
    st.session_state.instagram_text = st.text_area(
        "Instagram", value=st.session_state.instagram_text, height=280,
        label_visibility="collapsed", placeholder="Klicke auf 'Generieren' …"
    )

with tab_fb:
    st.caption(_char_indicator(st.session_state.facebook_text, LIMITS["facebook"]))
    st.session_state.facebook_text = st.text_area(
        "Facebook", value=st.session_state.facebook_text, height=280,
        label_visibility="collapsed", placeholder="Klicke auf 'Generieren' …"
    )

with tab_tt:
    st.caption(_char_indicator(st.session_state.tiktok_text, LIMITS["tiktok"]))
    st.session_state.tiktok_text = st.text_area(
        "TikTok", value=st.session_state.tiktok_text, height=280,
        label_visibility="collapsed", placeholder="Klicke auf 'Generieren' …"
    )

st.divider()

# ── Action buttons ────────────────────────────────────────────────────────────

has_content = bool(st.session_state.linkedin_text or st.session_state.instagram_text)

col_approve, col_post = st.columns([1, 1])

with col_approve:
    if st.button("📋 Zur Genehmigung senden", use_container_width=True,
                  disabled=not has_content):
        platforms = []
        content = {}
        if post_li and st.session_state.linkedin_text:
            platforms.append("linkedin")
            content["linkedin"] = st.session_state.linkedin_text
        if post_ig and st.session_state.instagram_text:
            platforms.append("instagram")
            content["instagram"] = st.session_state.instagram_text
        if post_fb and st.session_state.facebook_text:
            platforms.append("facebook")
            content["facebook"] = st.session_state.facebook_text
        if post_tt and st.session_state.tiktok_text:
            platforms.append("tiktok")
            content["tiktok"] = st.session_state.tiktok_text

        post_id = add_pending(
            topic=st.session_state.topic or topic,
            content=content,
            platforms=platforms,
        )
        st.success(f"✅ Post #{post_id} wartet auf Genehmigung — siehe ✅ Genehmigung")

with col_post:
    if st.button("📤 Direkt posten", use_container_width=True,
                  disabled=not has_content):
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

            if post_li and st.session_state.linkedin_text:
                try:
                    from src.linkedin_poster import post_to_linkedin
                    post_to_linkedin(st.session_state.linkedin_text, image_path)
                    successes.append("LinkedIn")
                except Exception as e:
                    errors.append(f"LinkedIn: {e}")

            if post_ig:
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

            if image_path and os.path.exists(image_path):
                os.unlink(image_path)

        if successes:
            st.success(f"✅ Gepostet auf: {', '.join(successes)}")
        if errors:
            st.error("\n".join(errors))
