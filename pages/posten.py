import streamlit as st
import os
import tempfile
from datetime import datetime, timedelta
from src import config as cfg
from src.post_store import LIMITS, add_pending

c = cfg.load()

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

# ── Sidebar (Status only) ─────────────────────────────────────────────────────

with st.sidebar:
    st.divider()

    connected = sum([
        bool(c.get("linkedin_access_token")),
        bool(str(c.get("instagram_access_token", "")).startswith("EAA")),
    ])
    pending_count = len([p for p in __import__("src.post_store", fromlist=["get_pending"]).get_pending()])
    st.caption(f"✅ {connected} von 2 Plattformen verbunden")
    if pending_count:
        st.warning(f"⏳ {pending_count} Post{'s' if pending_count > 1 else ''} wartet auf Genehmigung")

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

# Thema + Generieren
col_topic, col_btn = st.columns([4, 1])
with col_topic:
    topic = st.text_input("Thema", placeholder="Leer lassen für zufälliges Thema …",
                           label_visibility="collapsed")
with col_btn:
    generate = st.button("✨ Generieren", use_container_width=True, type="primary")

# Einstellungen-Zeile
col_plat, col_len, col_tone, col_ht, col_img = st.columns([2, 2, 2, 2, 1])

with col_plat:
    st.caption("Plattformen")
    post_li = st.checkbox("LinkedIn",  value=c.get("post_linkedin", True))
    post_ig = st.checkbox("Instagram", value=c.get("post_instagram", False))
    post_fb = st.checkbox("Facebook",  value=False)
    post_tt = st.checkbox("TikTok",    value=False)

with col_len:
    st.caption("Länge")
    length = st.radio(
        "Länge", ["Mini", "Kurz", "Mittel", "Lang", "Eigene"],
        index=["Mini", "Kurz", "Mittel", "Lang", "Eigene"].index(c.get("post_length", "Mittel"))
              if c.get("post_length", "Mittel") in ["Mini", "Kurz", "Mittel", "Lang"] else 2,
        label_visibility="collapsed",
    )
    custom_chars = None
    if length == "Eigene":
        custom_chars = st.number_input(
            "Zeichen", min_value=200, max_value=3000, value=500, step=50,
            label_visibility="collapsed",
        )
        st.markdown(
            f"<small style='color:gray'>{custom_chars} Zeichen ≈ {max(40, custom_chars // 5)} Wörter<br>"
            f"(Minimum: 200 Zeichen)</small>",
            unsafe_allow_html=True,
        )

with col_tone:
    st.caption("Ton")
    tone = st.radio(
        "Ton", ["Direkt", "Sachlich", "Storytelling", "Humorvoll", "Provokativ"],
        index=["Direkt", "Sachlich", "Storytelling", "Humorvoll", "Provokativ"].index(
            c.get("post_tone", "Direkt")
            if c.get("post_tone", "Direkt") in ["Direkt", "Sachlich", "Storytelling", "Humorvoll", "Provokativ"]
            else "Direkt"
        ),
        label_visibility="collapsed",
    )

with col_ht:
    st.caption("Hashtags")
    hashtags = st.select_slider(
        "Hashtags", options=[5, 8, 10, 12, 15],
        value=c.get("hashtag_count", 10),
        label_visibility="collapsed",
    )

with col_img:
    st.caption("Bild")
    use_image = st.toggle("DALL-E 3", value=c.get("generate_image", False),
                          label_visibility="collapsed")

st.divider()

if generate:
    if not c.get("openai_api_key"):
        st.error("OpenAI API Key fehlt — bitte in ⚙️ Einstellungen eintragen.")
    else:
        with st.spinner("Generiere Content …"):
            from src.content_generator import generate_content
            ig, li = generate_content(
                custom_topic=topic or None,
                length=length or "Mittel",
                tone=tone,
                hashtag_count=hashtags,
                custom_chars=custom_chars,
            )
            st.session_state.linkedin_text  = li["text"]
            st.session_state.instagram_text = ig["caption"]
            st.session_state.facebook_text  = li["text"]
            st.session_state.tiktok_text    = ig["caption"]
            st.session_state.topic          = ig["topic"]
            st.session_state.generated      = True
        st.success(f"Thema: **{ig['topic']}**")

# ── Preview tabs ──────────────────────────────────────────────────────────────

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

# ── Medien hochladen ──────────────────────────────────────────────────────────

st.subheader("Medien (optional)")
col_img_up, col_vid_up = st.columns(2)
with col_img_up:
    uploaded_image = st.file_uploader(
        "Bild hochladen", type=["jpg", "jpeg", "png", "webp"],
        help="Ersetzt das DALL-E Bild wenn ausgewählt"
    )
with col_vid_up:
    uploaded_video = st.file_uploader(
        "Video hochladen", type=["mp4", "mov", "avi"],
        help="Wird als Reel (Instagram) und Video-Post (LinkedIn) gepostet. Benötigt Cloudinary."
    )

if uploaded_video:
    st.info("📹 Video erkannt — wird als Reel auf Instagram und Video-Post auf LinkedIn gepostet.")

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
        st.caption("Hinweis: Hochgeladene Medien nur beim Direkt-Posten verfügbar.")

with col_post:
    if st.button("📤 Direkt posten", use_container_width=True,
                  disabled=not has_content):
        errors = []
        successes = []
        image_path = None
        video_path = None
        _tmp_files = []

        with st.spinner("Wird gepostet …"):
            if uploaded_video:
                tmp_v = tempfile.NamedTemporaryFile(
                    delete=False, suffix="." + uploaded_video.name.split(".")[-1]
                )
                tmp_v.write(uploaded_video.read())
                tmp_v.close()
                video_path = tmp_v.name
                _tmp_files.append(video_path)
            elif uploaded_image:
                tmp_i = tempfile.NamedTemporaryFile(
                    delete=False, suffix="." + uploaded_image.name.split(".")[-1]
                )
                tmp_i.write(uploaded_image.read())
                tmp_i.close()
                image_path = tmp_i.name
                _tmp_files.append(image_path)
            elif use_image and st.session_state.topic:
                try:
                    from src.image_generator import generate_image
                    image_path = generate_image(st.session_state.topic)
                    _tmp_files.append(image_path)
                except Exception as e:
                    errors.append(f"Bild: {e}")

            if post_li and st.session_state.linkedin_text:
                try:
                    from src.linkedin_poster import post_to_linkedin
                    post_to_linkedin(
                        st.session_state.linkedin_text,
                        image_path=image_path,
                        video_path=video_path,
                    )
                    successes.append("LinkedIn")
                except Exception as e:
                    errors.append(f"LinkedIn: {e}")

            if post_ig:
                if os.getenv("INSTAGRAM_ACCESS_TOKEN", "").startswith("EAA"):
                    try:
                        from src.instagram_poster import post_to_instagram
                        post_to_instagram(
                            st.session_state.instagram_text,
                            image_path=image_path,
                            video_path=video_path,
                        )
                        successes.append("Instagram")
                    except Exception as e:
                        errors.append(f"Instagram: {e}")
                else:
                    errors.append("Instagram: Token fehlt")

            if post_fb:
                errors.append("Facebook: noch nicht eingerichtet")
            if post_tt:
                errors.append("TikTok: noch nicht eingerichtet")

            for f in _tmp_files:
                if os.path.exists(f):
                    os.unlink(f)

        if successes:
            st.success(f"✅ Gepostet auf: {', '.join(successes)}")
        if errors:
            st.error("\n".join(errors))
