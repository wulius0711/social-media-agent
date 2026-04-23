from typing import Optional
import requests
import os
import time
from src.image_host import upload_to_imgbb, upload_to_cloudinary

BASE_URL = "https://graph.instagram.com/v21.0"


def post_to_instagram(
    caption: str,
    image_path: Optional[str] = None,
    video_path: Optional[str] = None,
) -> str:
    user_id = os.environ["INSTAGRAM_USER_ID"]
    token = os.environ["INSTAGRAM_ACCESS_TOKEN"]

    if video_path:
        public_url = upload_to_cloudinary(video_path)
        container_id = _create_reel_container(user_id, token, caption, public_url)
        _wait_for_container(token, container_id)
    elif image_path:
        public_url = upload_to_imgbb(image_path)
        container_id = _create_image_container(user_id, token, caption, public_url)
        time.sleep(3)
    else:
        raise ValueError("Instagram requires an image or video.")

    post_id = _publish_container(user_id, token, container_id)
    print(f"Instagram post published: {post_id}")
    return post_id


def _create_image_container(user_id: str, token: str, caption: str, image_url: str) -> str:
    response = requests.post(
        f"{BASE_URL}/{user_id}/media",
        params={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["id"]


def _create_reel_container(user_id: str, token: str, caption: str, video_url: str) -> str:
    response = requests.post(
        f"{BASE_URL}/{user_id}/media",
        params={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["id"]


def _wait_for_container(token: str, container_id: str, max_wait: int = 300):
    """Poll until Instagram finishes processing the video (max_wait seconds)."""
    for _ in range(max_wait // 5):
        time.sleep(5)
        r = requests.get(
            f"{BASE_URL}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        if r.ok:
            status = r.json().get("status_code", "")
            if status == "FINISHED":
                return
            if status == "ERROR":
                raise RuntimeError(f"Instagram video processing failed: {r.json()}")
    raise TimeoutError("Instagram video processing timed out.")


def _publish_container(user_id: str, token: str, container_id: str) -> str:
    response = requests.post(
        f"{BASE_URL}/{user_id}/media_publish",
        params={"creation_id": container_id, "access_token": token},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["id"]
