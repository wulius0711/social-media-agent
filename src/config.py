import json
import os
import platform
from pathlib import Path

APP_NAME = "WolfgangSocialAgent"

DEFAULTS = {
    # API Keys
    "openai_api_key": "",
    "imgbb_api_key": "",
    "cloudinary_cloud_name": "",
    "cloudinary_api_key": "",
    "cloudinary_api_secret": "",
    "instagram_user_id": "",
    "instagram_access_token": "",
    "linkedin_access_token": "",
    "linkedin_author_urn": "",
    # Business Profil
    "business_name": "",
    "business_description": "",
    "business_target": "",
    "business_tone_hints": "",
    "business_language": "Deutsch",
    # Post-Einstellungen
    "generate_image": False,
    "post_length": "Mittel",
    "post_tone": "Direkt",
    "hashtag_count": 10,
    "schedule_days": [2, 5],
    "schedule_hour": 10,
    "schedule_minute": 0,
    "post_instagram": False,
    "post_linkedin": True,
    "setup_complete": False,
}


def config_dir() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif platform.system() == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    d = base / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return config_dir() / "config.json"


def load() -> dict:
    p = config_path()
    if not p.exists():
        return DEFAULTS.copy()
    try:
        with open(p) as f:
            data = json.load(f)
        return {**DEFAULTS, **data}
    except Exception:
        return DEFAULTS.copy()


def save(cfg: dict):
    with open(config_path(), "w") as f:
        json.dump(cfg, f, indent=2)


def get(key: str):
    return load().get(key, DEFAULTS.get(key))


def set_val(key: str, value):
    cfg = load()
    cfg[key] = value
    save(cfg)


def apply_to_env():
    cfg = load()
    pairs = {
        "openai_api_key": "OPENAI_API_KEY",
        "imgbb_api_key": "IMGBB_API_KEY",
        "cloudinary_cloud_name": "CLOUDINARY_CLOUD_NAME",
        "cloudinary_api_key": "CLOUDINARY_API_KEY",
        "cloudinary_api_secret": "CLOUDINARY_API_SECRET",
        "instagram_user_id": "INSTAGRAM_USER_ID",
        "instagram_access_token": "INSTAGRAM_ACCESS_TOKEN",
        "linkedin_access_token": "LINKEDIN_ACCESS_TOKEN",
        "linkedin_author_urn": "LINKEDIN_AUTHOR_URN",
        "business_name": "BUSINESS_NAME",
        "business_description": "BUSINESS_DESCRIPTION",
        "business_target": "BUSINESS_TARGET",
        "business_tone_hints": "BUSINESS_TONE_HINTS",
        "business_language": "BUSINESS_LANGUAGE",
    }
    for k, env in pairs.items():
        # env var from GitHub Actions takes priority
        if not os.environ.get(env):
            v = cfg.get(k, "")
            if v:
                os.environ[env] = str(v)
    os.environ["GENERATE_IMAGE"] = os.environ.get("GENERATE_IMAGE", "true" if cfg.get("generate_image") else "false")
