"""
Image generation via Replicate (Flux Schnell model).
~$0.003 per image. Generates 7 unique images per carousel — one per slide.
"""

import os
import re


# Per-slide composition/mood variations — applied on top of the base prompt
# so each slide gets a genuinely different image
_SLIDE_VARIATIONS = [
    "dramatic close-up, extreme shadow and light contrast, intense atmosphere",
    "wide ethereal composition, cool deep blue tones, vast space",
    "split symmetrical view, electric light dividing two halves, violet tones",
    "warm amber and gold light, organic dissolving forms, crumbling edges",
    "full figure emerging from total darkness, single revelation light source",
    "minimal abstract, one concentrated glow at center, near-black background",
    "very dark cinematic, ultra-minimal, one soft light, final stillness",
]


def generate_image(prompt: str, content: dict, config: dict) -> str:
    """Generate a single image. Returns public HTTPS URL."""
    token = os.environ.get("REPLICATE_API_TOKEN") or config.get("replicate_api_token", "")
    if token:
        return _replicate(prompt, token, config)
    else:
        print("  No Replicate token — falling back to text image.")
        return _generate_text_image(content, config)


def generate_slide_images(base_prompt: str, config: dict, n_slides: int = 7) -> list:
    """
    Generate n_slides unique images, one per carousel slide.
    Each gets the base prompt + a slide-specific composition variation.
    Returns list of bytes objects (one per slide).
    """
    token = os.environ.get("REPLICATE_API_TOKEN") or config.get("replicate_api_token", "")
    if not token:
        raise RuntimeError("REPLICATE_API_TOKEN not set")

    bg_bytes_list = []
    for i in range(n_slides):
        variation = _SLIDE_VARIATIONS[i % len(_SLIDE_VARIATIONS)]
        prompt = f"{base_prompt.rstrip('. ')}. {variation}"
        print(f"    Generating image {i + 1}/{n_slides}...")
        url = _replicate(prompt, token, config)
        bg_bytes_list.append(download_image_bytes(url))

    return bg_bytes_list


def _replicate(prompt: str, token: str, config: dict) -> str:
    """Call Replicate Flux Schnell and return image URL."""
    import replicate

    base_style = config.get("midjourney_base_style", "")
    if base_style and base_style not in prompt:
        full_prompt = f"{prompt.rstrip('. ')}. {base_style}"
    else:
        full_prompt = prompt

    # Strip Midjourney-specific flags — not valid for Replicate
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

    if not output:
        raise ValueError("Replicate returned no output")
    url = str(output[0])
    if not url.startswith("http"):
        raise ValueError(f"Unexpected Replicate output: {url[:100]}")
    return url


def download_image_bytes(url: str) -> bytes:
    """Download image URL and return raw bytes."""
    import requests
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content


def _generate_text_image(content: dict, config: dict) -> str:
    from image_maker import create_image
    from pathlib import Path
    lines = [content.get(f"overlay_line{i}", "") for i in (1, 2, 3)]
    lines = [l for l in lines if l.strip()]
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)
    return create_image(lines, content.get("caption_main", "post")[:30],
                        config, output_path=str(out_dir / "latest_preview.png"))
