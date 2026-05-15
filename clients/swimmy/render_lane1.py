"""Swimmy Matcha — Lane 1 (Brand as character) hero still.
Standalone renderer. Calls Nano Banana 2 with the locked prompt.
Outputs PNG to clients/swimmy/.
"""
import base64
import os
import sys
from pathlib import Path
from google import genai
from google.genai import types

MODEL = "gemini-3.0-pro-image"  # will fallback / override below
NB2 = "gemini-3.1-flash-image-preview"
NB1 = "gemini-2.5-flash-image"

PROMPT = """A surreal hyperreal macro commercial photograph for a matcha cafe ad, shot in the style of high-end print advertising — Apple, Aesop, and Wieden+Kennedy energy. 4:5 vertical aspect ratio for Instagram (1080x1350).

A miniature female Olympic swimmer — black one-piece swimsuit, white silicone swim cap, mirrored chrome goggles — caught mid-freestyle stroke, gliding across the surface of a giant matcha latte. The matcha latte is served in a thick clear-glass cup that fills most of the frame. Her body is tiny relative to the cup; the cup is her swimming pool. Frothy matcha-green foam ripples around her body. A small splash kicks up where her left hand cuts the surface. Tiny green droplets suspended in mid-air, catching golden afternoon light.

The cup sits on a smooth oat-colored concrete table. Background is softly out of focus — minimalist Muscat cafe interior, terrazzo and bone-white walls, a single arched window casting warm 45-degree afternoon light from the left.

Camera: extreme macro, 100mm lens, f/2.8, very shallow depth of field. Swimmer in razor-sharp focus, foam slightly soft, background completely blurred.

Lighting: golden-hour Muscat afternoon. High contrast. Warm rim light catching the swimmer's wet skin and the rim of the glass. Cool matcha-green reflections bouncing onto her face from below.

Color palette is restricted: matcha green, warm cream, soft gold, deep shadow black. No other colors permitted.

INTEGRATED TEXT rendered inside the frame as part of the artwork (NOT a clean overlay):
- Upper-left: the lowercase phrase "dive in." in a clean modern sans-serif, off-white, restrained, magazine-ad scale.
- Just beneath, smaller, in elegant Arabic script: "اغمس"
- Lower-right corner: a discreet wordmark "swimmy" in lowercase — small, premium, like a brand signature on a poster.

Style: photorealistic, NOT illustrated, NOT cartoon. The single absurd element is the tiny swimmer. Everything else is grounded in real photography. Shot like a single still from a $250k commercial campaign. Witty, clean, premium, refreshing, cool."""


def render(model: str, out_path: Path) -> Path:
    api_key = os.environ.get("GEMINI_API") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API not set in env")
    client = genai.Client(api_key=api_key)
    print(f"calling {model}...")
    resp = client.models.generate_content(
        model=model,
        contents=PROMPT,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                data = inline.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                out_path.write_bytes(data)
                print(f"saved {out_path} ({len(data)//1024} KB)")
                return out_path
    raise RuntimeError(f"no image returned by {model}")


if __name__ == "__main__":
    out_dir = Path(__file__).parent
    model = sys.argv[1] if len(sys.argv) > 1 else NB2
    variant = sys.argv[2] if len(sys.argv) > 2 else "v1"
    render(model, out_dir / f"lane1_{variant}.png")
