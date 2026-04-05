"""
Image generation via Google Imagen 3 (Gemini API).
Much higher quality than Replicate Flux for cinematic/photorealistic imagery.
~$0.04 per image. 7 images per carousel = ~$0.28/post.

API key: set GEMINI_API environment variable (GitHub Secret).
"""

import base64
import os
import time
import requests

_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "imagen-3.0-generate-001:predict"
)

# Per-slide composition variations — layered on top of the base prompt
_SLIDE_VARIATIONS = [
    "dramatic close-up, extreme shadow and light contrast, intense atmosphere",
    "wide ethereal composition, cool deep blue tones, vast cosmic space",
    "split symmetrical composition, electric light dividing two halves, violet tones",
    "warm amber and gold light, organic dissolving forms, crumbling stone edges",
    "full figure emerging from total darkness, single revelation light source",
    "minimal abstract, one concentrated glow at center, near-black background",
    "very dark cinematic, ultra-minimal, one soft light, final stillness",
]


def generate_slide_images(base_prompt: str, config: dict, n_slides: int = 7) -> list:
    """
    Generate n_slides images via Imagen 3, one per carousel slide.
    Returns list of bytes objects.
    """
    api_key = os.environ.get("GEMINI_API") or config.get("google_api_key", "")
    if not api_key:
        raise RuntimeError("GEMINI_API not set")

    bg_bytes_list = []
    for i in range(n_slides):
        variation = _SLIDE_VARIATIONS[i % len(_SLIDE_VARIATIONS)]
        prompt = f"{base_prompt.rstrip('. ')}. {variation}"
        print(f"    Generating image {i + 1}/{n_slides} via Imagen 3...")
        img_bytes = _imagen3(prompt, api_key)
        bg_bytes_list.append(img_bytes)
        if i < n_slides - 1:
            time.sleep(2)  # Imagen 3 is fast, small buffer is enough

    return bg_bytes_list


def _imagen3(prompt: str, api_key: str) -> bytes:
    """Call Imagen 3 and return raw image bytes."""
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1",
            "safetySetting": "block_only_high",
            "personGeneration": "allow_adult",
        },
    }

    resp = requests.post(
        _GEMINI_URL,
        params={"key": api_key},
        json=payload,
        timeout=60,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Imagen 3 error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        b64 = data["predictions"][0]["bytesBase64Encoded"]
        return base64.b64decode(b64)
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Imagen 3 response: {data}") from e
