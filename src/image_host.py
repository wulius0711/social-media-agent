import requests
import base64
import os


def upload_to_imgbb(image_path: str) -> str:
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


def upload_to_cloudinary(file_path: str) -> str:
    """Upload image or video to Cloudinary and return public URL."""
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
    )

    is_video = file_path.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))
    resource_type = "video" if is_video else "image"

    result = cloudinary.uploader.upload(
        file_path,
        resource_type=resource_type,
        folder="social-agent",
    )
    return result["secure_url"]
