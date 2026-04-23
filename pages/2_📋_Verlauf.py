import streamlit as st
from src import post_store

st.title("📋 Verlauf")

STATUS_ICON = {
    "pending":  "⏳ Ausstehend",
    "approved": "✅ Genehmigt",
    "posted":   "📤 Gepostet",
    "rejected": "❌ Abgelehnt",
}

all_posts = post_store.get_all()

if not all_posts:
    st.info("Noch keine Posts erstellt.")
    st.stop()

# Filter + Alle löschen in einer Zeile
col_filter, col_del = st.columns([5, 1])
with col_filter:
    filter_status = st.multiselect(
        "Status",
        options=list(STATUS_ICON.keys()),
        default=list(STATUS_ICON.keys()),
        format_func=lambda x: STATUS_ICON[x],
        label_visibility="collapsed",
    )
with col_del:
    if st.button("🗑️ Alle löschen", use_container_width=True):
        post_store.delete_all()
        st.rerun()

filtered = [p for p in all_posts if p["status"] in filter_status]
st.caption(f"{len(filtered)} von {len(all_posts)} Posts")
st.divider()

for post in filtered:
    status = post["status"]
    icon = STATUS_ICON.get(status, status)
    date = post["created_at"][:16].replace("T", " ")
    platforms = ", ".join(p.capitalize() for p in post.get("platforms", []))

    with st.expander(f"{icon} · {date} · {post.get('topic', '—')[:60]} · {platforms}"):
        content = post.get("content", {})
        if content:
            tabs = st.tabs([p.capitalize() for p in content.keys()])
            for tab, (platform, text) in zip(tabs, content.items()):
                with tab:
                    st.text_area("", value=text, height=180,
                                  disabled=True, label_visibility="collapsed",
                                  key=f"hist_{post['id']}_{platform}")

        if post.get("rejection_reason"):
            st.error(f"Ablehnungsgrund: {post['rejection_reason']}")
        if post.get("posted_at"):
            st.caption(f"Gepostet: {post['posted_at'][:16].replace('T', ' ')}")

        if st.button("🗑️ Löschen", key=f"del_{post['id']}"):
            post_store.delete(post["id"])
            st.rerun()
