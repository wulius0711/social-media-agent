import streamlit as st
import os
from src import config as cfg
from src import post_store

cfg.apply_to_env()

st.set_page_config(page_title="Genehmigung", page_icon="✅", layout="wide")
st.title("✅ Genehmigung")

pending = post_store.get_pending()

if not pending:
    st.info("Keine Posts ausstehend — alles erledigt! 🎉")
    st.stop()

st.caption(f"{len(pending)} Post{'s' if len(pending) > 1 else ''} wartet auf deine Freigabe.")

for post in pending:
    with st.container(border=True):
        col_meta, col_action = st.columns([3, 1])

        with col_meta:
            st.markdown(f"**#{post['id']}** · {post['created_at'][:16].replace('T', ' ')} · "
                        f"Thema: *{post.get('topic', '—')}*")
            platforms_str = ", ".join(p.capitalize() for p in post.get("platforms", []))
            st.caption(f"Plattformen: {platforms_str}")

        with col_action:
            st.write("")

        # Content tabs
        platforms = post.get("platforms", [])
        content = post.get("content", {})

        if len(platforms) > 1:
            tabs = st.tabs([p.capitalize() for p in platforms])
            for tab, platform in zip(tabs, platforms):
                with tab:
                    char_limit = post_store.LIMITS.get(platform, 3000)
                    text = content.get(platform, "")
                    st.caption(f"{len(text):,} / {char_limit:,} Zeichen")
                    new_text = st.text_area(
                        f"Text {platform}", value=text, height=200,
                        label_visibility="collapsed", key=f"edit_{post['id']}_{platform}"
                    )
                    content[platform] = new_text
        elif platforms:
            platform = platforms[0]
            char_limit = post_store.LIMITS.get(platform, 3000)
            text = content.get(platform, "")
            st.caption(f"{len(text):,} / {char_limit:,} Zeichen")
            new_text = st.text_area(
                f"Text", value=text, height=200,
                label_visibility="collapsed", key=f"edit_{post['id']}_{platform}"
            )
            content[platform] = new_text

        st.divider()
        col_reject, col_spacer, col_approve, col_post = st.columns([2, 1, 1, 1])

        with col_reject:
            reason = st.text_input("Ablehnungsgrund (optional)",
                                    key=f"reason_{post['id']}",
                                    placeholder="z.B. Ton passt nicht …",
                                    label_visibility="collapsed")
            if st.button("❌ Ablehnen", key=f"reject_{post['id']}", use_container_width=True):
                post_store.reject(post["id"], reason)
                st.rerun()

        with col_approve:
            if st.button("✅ Genehmigen", key=f"approve_{post['id']}", use_container_width=True):
                post_store.update_content(post["id"], content)
                post_store.approve(post["id"])
                st.success(f"Post #{post['id']} genehmigt!")
                st.rerun()

        with col_post:
            if st.button("📤 Genehmigen & Posten", key=f"post_{post['id']}",
                          use_container_width=True, type="primary"):
                post_store.update_content(post["id"], content)
                errors = []
                successes = []

                with st.spinner("Wird gepostet …"):
                    if "linkedin" in platforms and content.get("linkedin"):
                        try:
                            from src.linkedin_poster import post_to_linkedin
                            post_to_linkedin(content["linkedin"])
                            successes.append("LinkedIn")
                        except Exception as e:
                            errors.append(f"LinkedIn: {e}")

                    if "instagram" in platforms:
                        if os.getenv("INSTAGRAM_ACCESS_TOKEN", "").startswith("EAA"):
                            try:
                                from src.instagram_poster import post_to_instagram
                                post_to_instagram(content.get("instagram", ""))
                                successes.append("Instagram")
                            except Exception as e:
                                errors.append(f"Instagram: {e}")
                        else:
                            errors.append("Instagram: Token fehlt")

                if successes:
                    post_store.mark_posted(post["id"])
                    st.success(f"✅ Gepostet auf: {', '.join(successes)}")
                    st.rerun()
                if errors:
                    st.error("\n".join(errors))
