import openai
import requests
import os
import tempfile
from pathlib import Path

client = openai.OpenAI()

IMAGE_STYLE = (
    "Minimalist, high-end web design aesthetic. Clean composition, "
    "Austrian/European design sensibility. Professional, no people, no text in image. "
    "Muted tones with one accent color. Studio photography style."
)


def generate_image(topic: str) -> str | None:
    prompt = (
        f"Abstract visual concept representing: {topic}. "
        f"{IMAGE_STYLE} "
        "Square format, social media ready."
    )

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    return _download_image(image_url)


def _download_image(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.write(response.content)
    tmp.close()
    return tmp.name
