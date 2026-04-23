from typing import Optional
import requests
import os
import time

BASE_URL = "https://api.linkedin.com/v2"


def post_to_linkedin(
    text: str,
    image_path: Optional[str] = None,
    video_path: Optional[str] = None,
) -> str:
    token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    author = os.environ["LINKEDIN_AUTHOR_URN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    if video_path:
        asset_urn = _upload_video(headers, author, video_path)
        post_id = _create_post_with_media(headers, author, text, asset_urn, "VIDEO")
    elif image_path:
        asset_urn = _upload_image(headers, author, image_path)
        post_id = _create_post_with_media(headers, author, text, asset_urn, "IMAGE")
    else:
        post_id = _create_text_post(headers, author, text)

    print(f"LinkedIn post published: {post_id}")
    return post_id


def _upload_image(headers: dict, author: str, image_path: str) -> str:
    register_resp = requests.post(
        f"{BASE_URL}/assets?action=registerUpload",
        headers=headers,
        json={
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        },
        timeout=30,
    )
    register_resp.raise_for_status()
    data = register_resp.json()
    upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = data["value"]["asset"]

    with open(image_path, "rb") as f:
        requests.put(
            upload_url,
            data=f,
            headers={"Authorization": headers["Authorization"]},
            timeout=60,
        ).raise_for_status()

    return asset_urn


def _upload_video(headers: dict, author: str, video_path: str) -> str:
    # Step 1: Register upload
    register_resp = requests.post(
        f"{BASE_URL}/assets?action=registerUpload",
        headers=headers,
        json={
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-video"],
                "owner": author,
                "serviceRelationships": [{
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }]
            }
        },
        timeout=30,
    )
    register_resp.raise_for_status()
    data = register_resp.json()
    upload_url = data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
    asset_urn = data["value"]["asset"]

    # Step 2: Upload binary
    with open(video_path, "rb") as f:
        requests.put(
            upload_url,
            data=f,
            headers={
                "Authorization": headers["Authorization"],
                "Content-Type": "application/octet-stream",
            },
            timeout=300,
        ).raise_for_status()

    # Step 3: Poll until processing complete (max 3 min)
    asset_id = asset_urn.split(":")[-1]
    for _ in range(36):
        time.sleep(5)
        status_resp = requests.get(
            f"{BASE_URL}/assets/{asset_id}",
            headers=headers,
            timeout=30,
        )
        if status_resp.ok:
            status = status_resp.json().get("recipes", [{}])[0].get("status", "")
            if status == "AVAILABLE":
                break

    return asset_urn


def _create_post_with_media(headers: dict, author: str, text: str, asset_urn: str, media_type: str) -> str:
    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": media_type,
                "media": [{"status": "READY", "media": asset_urn}]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    return _post_ugc(headers, payload)


def _create_text_post(headers: dict, author: str, text: str) -> str:
    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    return _post_ugc(headers, payload)


def _post_ugc(headers: dict, payload: dict) -> str:
    response = requests.post(f"{BASE_URL}/ugcPosts", headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.headers.get("x-restli-id", "unknown")
