"""
Image generation via Google Gemini 2.0 Flash (image generation model).
Uses direct REST API — no SDK version issues.

API key: set GEMINI_API environment variable (GitHub Secret).
"""

import base64
import os
import time
import requests

_GEMINI_IMG_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash-exp:generateContent"
)

# Per-slide composition variations for Neoclassical Surrealism / Vaporwave / Dreamcore
_SLIDE_VARIATIONS = [
    "dramatic close-up bust, glowing jagged rift down the center revealing deep space nebula inside, cyan and magenta rim lighting, chromatic aberration edges",
    "wide shot full-body kneeling marble figure, vertical beam of white light splitting two halves, dark void background, vibrant pink and yellow wildflowers at base, volumetric lighting",
    "left half molten volcanic red obsidian, right half pristine white marble in golden light, electric blue lightning bolt splitting center, lush dew-covered flowers, high chiaroscuro",
    "ancient Roman bust, one half cracked and weathered stone in warm amber, other half smooth marble in cold blue-violet, cosmic starfield visible through the crack, synthwave color palette",
    "full figure marble statue fragmenting into neon light shards, bioluminescent flora surrounding the base, deep black void, ray-traced reflections, surrealist masterpiece",
    "extreme close-up marble face, one eye cosmic void with stars, other eye intact stone, magenta and teal rim light, chromatic aberration, moody cinematic atmosphere",
    "dark minimal, single marble torso dissolving into starfield at the edges, soft warm glow at center, wildflowers fading into darkness at base, final stillness",
]


def generate_slide_images(base_prompt: str, config: dict, n_slides: int = 7) -> list:
    """Generate n_slides images. Returns list of bytes objects."""
    api_key = os.environ.get("GEMINI_API") or config.get("google_api_key", "")
    if not api_key:
        raise RuntimeError("GEMINI_API not set")

    bg_bytes_list = []
    for i in range(n_slides):
        variation = _SLIDE_VARIATIONS[i % len(_SLIDE_VARIATIONS)]
        prompt = f"{base_prompt.rstrip('. ')}. {variation}"
        print(f"    Generating image {i + 1}/{n_slides} via Gemini Imagen...")
        img_bytes = _generate(prompt, api_key)
        bg_bytes_list.append(img_bytes)
        if i < n_slides - 1:
            time.sleep(2)

    return bg_bytes_list


def _generate(prompt: str, api_key: str) -> bytes:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    resp = requests.post(
        _GEMINI_IMG_URL,
        params={"key": api_key},
        json=payload,
        timeout=60,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Gemini image error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        parts = data["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        raise RuntimeError(f"No image in response: {data}")
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected response structure: {data}") from e
