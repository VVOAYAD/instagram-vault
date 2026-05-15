"""Swimmy Lane 1 v2 — locked to their actual DNA (pool tile, editorial fashion, deli label)."""
import base64, os, sys
from pathlib import Path
from google import genai
from google.genai import types

NB2 = "gemini-3.1-flash-image-preview"

PROMPT = """Editorial fashion commercial photograph, 4:5 vertical (1080x1350), Y2K-meets-matcha, Tokyo swim-club energy. Cool flat studio light. Strong clean shadows. NOT golden hour. NOT minimalist Aesop.

A confident young Omani woman, mid-20s, glossy dark hair, sleek white sleeveless tee, thin gold chain, oversized chrome aviator sunglasses. Slight smirk. Holding a giant clear-glass mug of iced matcha latte directly toward the camera with both hands at chest height. The mug fills a third of the frame, foregrounded.

Inside the matcha, floating on the surface, a TINY miniature female Olympic swimmer — black swimsuit, white silicone cap, mirrored goggles — caught mid-freestyle stroke. The swimmer is small (1/8 the cup width) and clearly photoreal — the cup is her swimming pool. Tiny green splash where her hand cuts the foam.

ON the front of the glass mug: a white rectangular deli-sticker label with serrated edges. On the label, hand-drawn black ink: "swimmy" wordmark at top in retro bubble-script, then "HONEY SALTED VANILLA" hand-printed all-caps with underline, then small print "ESSENTIAL FOR A BETTER MOOD / MADINAT AS SULTAN QABOOS ST / MUSCAT, OMAN". The label is sharp, readable.

BACKGROUND: a flat wall of small square pool tiles in soft cyan / duck-egg blue (#A8C8D8), grid grout lines visible. The wall fills the frame edge to edge. Some condensation on the cup.

Color palette restricted: pool-tile cyan blue, matcha green, white, soft skin tones, deep navy. NO warm gold, NO cream, NO terrazzo.

INTEGRATED IN-FRAME TEXT, rendered as part of the artwork:
- Upper left: hand-drawn black marker style, lowercase "dive in." Casual, slightly imperfect line weight.
- Right beneath it, smaller, in confident Arabic marker script: "اغمس"
- Bottom-right corner: the "swimmy" retro 70s soft-bubble wordmark in white, with tiny "matcha" tagline beneath in clean small sans.

Style: editorial fashion still, like a print ad in i-D or Wonderland magazine crossed with a Tokyo matcha brand. Sharp, witty, premium-playful. Photorealistic. The single absurd element is the tiny swimmer in the cup."""


def render(out_path: Path) -> Path:
    api_key = os.environ.get("GEMINI_API")
    if not api_key:
        raise SystemExit("GEMINI_API not set")
    client = genai.Client(api_key=api_key)
    print(f"calling {NB2}...")
    resp = client.models.generate_content(
        model=NB2,
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
    raise RuntimeError("no image returned")


if __name__ == "__main__":
    variant = sys.argv[1] if len(sys.argv) > 1 else "v2"
    render(Path(__file__).parent / f"lane1_{variant}.png")
