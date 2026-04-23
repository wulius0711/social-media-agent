import json
import uuid
from datetime import datetime
from src.config import config_dir

LIMITS = {
    "linkedin":  3000,
    "instagram": 2200,
    "facebook":  63000,
    "tiktok":    2200,
}


def _path():
    return config_dir() / "posts.json"


def _load() -> list:
    p = _path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except Exception:
        return []


def _save(posts: list):
    _path().write_text(json.dumps(posts, indent=2, ensure_ascii=False))


def add_pending(topic: str, content: dict, platforms: list) -> str:
    posts = _load()
    post = {
        "id": str(uuid.uuid4())[:8],
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "topic": topic,
        "status": "pending",
        "platforms": platforms,
        "content": content,
        "approved_at": None,
        "posted_at": None,
        "rejection_reason": None,
    }
    posts.insert(0, post)
    _save(posts)
    return post["id"]


def get_all() -> list:
    return _load()


def get_pending() -> list:
    return [p for p in _load() if p["status"] == "pending"]


def approve(post_id: str):
    posts = _load()
    for p in posts:
        if p["id"] == post_id:
            p["status"] = "approved"
            p["approved_at"] = datetime.now().isoformat(timespec="seconds")
    _save(posts)


def reject(post_id: str, reason: str = ""):
    posts = _load()
    for p in posts:
        if p["id"] == post_id:
            p["status"] = "rejected"
            p["rejection_reason"] = reason
    _save(posts)


def mark_posted(post_id: str):
    posts = _load()
    for p in posts:
        if p["id"] == post_id:
            p["status"] = "posted"
            p["posted_at"] = datetime.now().isoformat(timespec="seconds")
    _save(posts)


def update_content(post_id: str, content: dict):
    posts = _load()
    for p in posts:
        if p["id"] == post_id:
            p["content"] = content
    _save(posts)


def delete(post_id: str):
    posts = _load()
    _save([p for p in posts if p["id"] != post_id])


def delete_all():
    _save([])
