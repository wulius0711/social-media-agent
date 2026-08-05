from typing import Optional
import openai
import requests
import os
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

client = openai.OpenAI()

IMAGE_STYLE = (
    "Minimalist, high-end web design aesthetic. Clean composition, "
    "Austrian/European design sensibility. Professional, no people, no text in image. "
    "Muted tones with one accent color. Studio photography style."
)


def generate_image(topic: str) -> Optional[str]:
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
    _watermark(tmp.name)
    return tmp.name


def _watermark(path: str) -> None:
    """Art. 50 Abs. 2 AI Act: KI-generierte Bilder muessen als solche erkennbar sein."""
    img = Image.open(path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    label = "KI-generiert"
    font_size = max(18, img.width // 40)
    font = None
    for font_path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ):
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    padding = font_size // 2
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    box_w, box_h = text_w + padding * 2, text_h + padding * 2
    x = img.width - box_w - padding
    y = img.height - box_h - padding

    draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=box_h // 4, fill=(0, 0, 0, 150))
    draw.text((x + padding, y + padding - bbox[1]), label, font=font, fill=(255, 255, 255, 235))

    Image.alpha_composite(img, overlay).convert("RGB").save(path, "PNG")
