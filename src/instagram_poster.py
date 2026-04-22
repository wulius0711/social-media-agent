import requests
import os
import time
from src.image_host import upload_to_imgbb


BASE_URL = "https://graph.instagram.com/v21.0"


def post_to_instagram(caption: str, image_path: str | None = None) -> str:
    user_id = os.environ["INSTAGRAM_USER_ID"]
    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

    if image_path:
        public_url = upload_to_imgbb(image_path)
        container_id = _create_media_container(user_id, token, caption, public_url)
    else:
        # Text-only not supported on Instagram feed — use placeholder
        raise ValueError("Instagram requires an image. Set GENERATE_IMAGE=true.")

    # Instagram recommends waiting briefly before publishing
    time.sleep(3)
    post_id = _publish_container(user_id, token, container_id)
    print(f"Instagram post published: {post_id}")
    return post_id


def _create_media_container(user_id: str, token: str, caption: str, image_url: str) -> str:
    response = requests.post(
        f"{BASE_URL}/{user_id}/media",
        params={
            "image_url": image_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["id"]


def _publish_container(user_id: str, token: str, container_id: str) -> str:
    response = requests.post(
        f"{BASE_URL}/{user_id}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": token,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["id"]
