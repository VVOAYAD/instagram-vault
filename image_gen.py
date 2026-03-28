"""
Image generation via Replicate (Flux Schnell model).
~$0.003 per image. Returns a public URL Instagram can use directly.
"""

import os
import re


def generate_image(midjourney_prompt: str, content: dict, config: dict) -> str:
    """
    Generate an image from a prompt.
    Returns a public HTTPS URL of the generated image.

    Falls back to text-overlay image (Pillow) if Replicate not configured.
    """
    token = os.environ.get("REPLICATE_API_TOKEN") or config.get("replicate_api_token", "")

    if token:
        return _generate_with_replicate(midjourney_prompt, token, config)
    else:
        print("⚠️  No Replicate token — falling back to text image.")
        return _generate_text_image(content, config)


def _generate_with_replicate(prompt: str, token: str, config: dict) -> str:
    """Call Replicate's Flux Schnell model."""
    import replicate

    # Add the base style from config to every prompt
    base_style = config.get("midjourney_base_style", "")
    if base_style and base_style not in prompt:
        full_prompt = f"{prompt.rstrip('. ')}. {base_style}"
    else:
        full_prompt = prompt

    # Strip Midjourney-specific flags (--ar, --v, etc.) — not valid for Replicate
    full_prompt = re.sub(r"--\w+\s[\w.]+", "", full_prompt).strip()

    client = replicate.Client(api_token=token)
    output = client.run(
        "black-forest-labs/flux-schnell",
        input={
            "prompt": full_prompt,
            "aspect_ratio": "1:1",
            "output_format": "jpg",
            "output_quality": 95,
            "num_outputs": 1,
            "go_fast": True,
        },
    )

    # Replicate returns a list of FileOutput objects; str() gives the URL
    if not output:
        raise ValueError("Replicate returned no output")

    image_url = str(output[0])
    if not image_url.startswith("http"):
        raise ValueError(f"Unexpected Replicate output: {image_url[:100]}")

    return image_url


def download_image_bytes(url: str) -> bytes:
    """Download an image URL and return raw bytes (for carousel slide 1 background)."""
    import requests
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content


def _generate_text_image(content: dict, config: dict) -> str:
    """
    Fallback: create a local typographic image using Pillow.
    Returns local file path (only works for local/dry-run, not Instagram posting).
    """
    from image_maker import create_image
    from pathlib import Path
    import tempfile

    lines = [content.get(f"overlay_line{i}", "") for i in (1, 2, 3)]
    lines = [l for l in lines if l.strip()]
    title = content.get("caption_main", "post")[:30]

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = str(out_dir / "latest_preview.png")

    return create_image(lines, title, config, output_path=out_path)
