import requests
import base64
import os


def upload_to_imgbb(image_path: str) -> str:
    """Upload image to imgbb and return public URL (required by Instagram API)."""
    api_key = os.environ["IMGBB_API_KEY"]

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "image": image_data},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"]["url"]
