"""
Image generation via Google Imagen 3 (Gemini API).
Uses google-generativeai SDK with imagen-3.0-generate-001 model.

API key: set GEMINI_API environment variable (GitHub Secret).
"""

import os
import time
import io

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
    """Generate n_slides images via Imagen 3. Returns list of bytes objects."""
    api_key = os.environ.get("GEMINI_API") or config.get("google_api_key", "")
    if not api_key:
        raise RuntimeError("GEMINI_API not set")

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.ImageGenerationModel("imagen-3.0-generate-001")

    bg_bytes_list = []
    for i in range(n_slides):
        variation = _SLIDE_VARIATIONS[i % len(_SLIDE_VARIATIONS)]
        prompt = f"{base_prompt.rstrip('. ')}. {variation}"
        print(f"    Generating image {i + 1}/{n_slides} via Imagen 3...")

        result = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_only_high",
            person_generation="allow_adult",
        )

        img = result.images[0]
        buf = io.BytesIO()
        img._pil_image.save(buf, format="JPEG", quality=95)
        bg_bytes_list.append(buf.getvalue())

        if i < n_slides - 1:
            time.sleep(1)

    return bg_bytes_list
