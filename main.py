#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from pathlib import Path

from src import config as cfg
cfg.apply_to_env()

_handlers = [logging.StreamHandler()]
if sys.platform == "darwin":
    _log_dir = Path.home() / "Library" / "Logs"
    _log_dir.mkdir(parents=True, exist_ok=True)
    _handlers.append(logging.FileHandler(_log_dir / "WolfgangSocialAgent.log"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=_handlers,
)
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default=None)
    args = parser.parse_args()

    c = cfg.load()
    from src.content_generator import generate_content
    from src.image_generator import generate_image
    from src.instagram_poster import post_to_instagram
    from src.linkedin_poster import post_to_linkedin

    log.info("=== Social Media Agent gestartet ===")
    if args.topic:
        log.info(f"Thema: {args.topic}")

    ig, li = generate_content(
        custom_topic=args.topic,
        length=c.get("post_length", "Mittel"),
        tone=c.get("post_tone", "Direkt"),
        hashtag_count=c.get("hashtag_count", 10),
    )
    log.info(f"Thema generiert: {ig['topic']}")

    image_path = None
    if c.get("generate_image"):
        try:
            image_path = generate_image(ig["topic"])
            log.info(f"Bild erstellt: {image_path}")
        except Exception as e:
            log.warning(f"Bild fehlgeschlagen: {e}")

    if c.get("post_linkedin"):
        try:
            post_to_linkedin(li["text"], image_path)
        except Exception as e:
            log.error(f"LinkedIn: {e}")

    if c.get("post_instagram") and os.getenv("INSTAGRAM_ACCESS_TOKEN", "").startswith("EAA"):
        try:
            post_to_instagram(ig["caption"], image_path)
        except Exception as e:
            log.error(f"Instagram: {e}")

    if image_path and os.path.exists(image_path):
        os.unlink(image_path)

    log.info("=== Fertig ===")


if __name__ == "__main__":
    main()
