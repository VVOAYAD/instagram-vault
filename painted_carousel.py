"""Painted-lane carousel generator (fallenpoe-style).
Generates all 7 slides for one carousel into output/test_slides/<stamp>/.
Does NOT post anywhere. Cost ~$0.14 per full carousel (Nano Banana 1).
"""
from __future__ import annotations
import base64, datetime as dt, os, sys, time
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REFS_DIR = None  # set after ROOT is defined below

ROOT = Path(__file__).parent
STYLES_ROOT = ROOT / "styles"
DEFAULT_STYLE = "painted"
REFS_DIR: Path | None = None  # set in main() after style arg is parsed
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API = os.environ.get("GEMINI_API")
if not API:
    print("ERROR: GEMINI_API missing in .env"); sys.exit(1)

# --------- DNA — short directive; the REFERENCE IMAGES carry the visual DNA ---------
DNA = (
    "Vertical 4:5 portrait. MATCH THE STYLE of the reference images EXACTLY — same painterly "
    "technique, same brushwork, same palette, same texture, same vintage warm tones, same "
    "naive-figurative illustration feel, same paper/canvas grain. Treat the refs as the source "
    "of truth for visual DNA. NO TEXT in the image."
)


def load_refs() -> list[types.Part]:
    if not REFS_DIR or not REFS_DIR.exists():
        return []
    imgs = sorted(p for p in REFS_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    parts = []
    for p in imgs:
        mime = "image/jpeg" if p.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    return parts

# --------- 7 slides — (scene_prompt, [text_lines]) ---------
SLIDES = [
    # 1 — cover (hook)
    (
        "Foreground: a young woman alone on a worn dark velvet couch in a dimly lit room, knees "
        "drawn up, hands folded in her lap, head tilted slightly down. A single candle on a side "
        "table casts warm amber light across her face. Heavy curtains, antique wallpaper. The "
        "room feels empty around her. Solitary, intimate, melancholic.",
        ["the cost of being", "everyone's safe place"],
    ),
    # 2 — name (people-pleasing as costume)
    (
        "Foreground close-up: a young woman holding a delicate theatrical paper mask of a "
        "smiling serene face, lifted halfway to cover the upper half of her own face. Her real "
        "expression below the mask is weary and quiet. Soft amber light from one side, deep "
        "shadows. A vanity table behind her with a small mirror and unlit candle.",
        ["people-pleasing isn't kindness.", "it's a survival strategy", "wearing kindness as a costume."],
    ),
    # 3 — root (childhood, love came with usefulness)
    (
        "A small child, maybe six years old, carries a heavy silver tea tray with porcelain cups "
        "across a long candlelit dining room toward distant adult figures seated in deep shadow "
        "at the far end of the room. The child is dwarfed by the tray. Reverent, burdened. Warm "
        "candle glow on the child, the adults remain silhouettes.",
        ["somewhere early, you learned", "love came with usefulness.", "so being needed felt", "safer than being known."],
    ),
    # 4 — mistake (i just love helping vs scared to be seen)
    (
        "Close-up at a candlelit wooden table: a woman is gently bandaging another person's "
        "outstretched hand with white linen — but her own hands, holding the bandage, have small "
        "unbandaged cuts and bruises she hasn't tended to. Warm amber candlelight, dark room, "
        "intimate two-figure scene. Her face soft and focused on the other.",
        ["you call it 'i just love helping.'", "under it:", "'i'm scared of being seen", "when i'm not useful.'"],
    ),
    # 5 — cost (function not presence) — already proven, regenerated for set consistency
    (
        "Foreground: a pair of feminine hands and forearms, sleeves rolled to the elbow, pouring "
        "a steaming pot of tea into four porcelain cups on a wooden tray. Background: a dim "
        "candlelit dining room, four blurred guests around a dark wooden table, all turned "
        "toward each other deep in conversation, none looking at the hands serving them. "
        "Candles between them, soft warm bokeh.",
        ["they miss your function.", "not your presence."],
    ),
    # 6 — the move (let one person see you tired)
    (
        "Foreground: a woman with closed eyes resting her head on the lap of another seated "
        "figure beside a stone fireplace. The seated person's hand rests gently on her hair, no "
        "words exchanged. Soft firelight glow on both, room in warm shadow. Stillness. No fixing, "
        "just presence.",
        ["let one person see you tired", "without fixing it for them.", "no apology. no joke.", "just sit in their gaze.", "that's the rep."],
    ),
    # 7 — close + cta (people who only loved you sturdy)
    (
        "Foreground: a woman asleep on a couch under soft afternoon light streaming through tall "
        "windows, blanket half-pulled over her, peaceful. Background: in another corner of the "
        "room, two or three blurred figures stand awkwardly with their coats, glancing toward "
        "her, unsure, one already half-turned to leave through a doorway. Warm muted tones.",
        ["the people who only loved you sturdy", "will struggle when you rest.", "let them.", "that's how you find out", "who's actually here."],
    ),
]

today = dt.datetime.now().strftime("%Y-%m-%d")
SET_DIR = ROOT / "output" / today
SET_DIR.mkdir(parents=True, exist_ok=True)

client = genai.Client(api_key=API)
FONT_PATH = str(ROOT / "fonts" / "PlayfairDisplay-Italic.ttf")


def overlay_text(img: Image.Image, lines: list[str]) -> Image.Image:
    img = img.convert("RGBA")
    W, H = img.size
    font_size = int(H * 0.045) if len(lines) <= 3 else int(H * 0.038)
    font = ImageFont.truetype(FONT_PATH, font_size)

    text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    line_gap = int(font_size * 0.4)
    total_h = len(lines) * font_size + (len(lines) - 1) * line_gap
    y = int(H * 0.80) - total_h // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 240))
        y += font_size + line_gap

    glow = text_layer.filter(ImageFilter.GaussianBlur(radius=int(font_size * 0.25)))
    img = Image.alpha_composite(img, glow)
    img = Image.alpha_composite(img, text_layer)
    return img.convert("RGB")


_REFS_CACHE: list[types.Part] | None = None


def _refs() -> list[types.Part]:
    global _REFS_CACHE
    if _REFS_CACHE is None:
        _REFS_CACHE = load_refs()
        print(f"  loaded {len(_REFS_CACHE)} style refs from {REFS_DIR.name}")
    return _REFS_CACHE


def gen_one(idx: int, scene: str, lines: list[str]):
    prompt = f"{DNA}\n\nScene: {scene}"
    print(f"[slide {idx}] generating...")
    contents: list = [*_refs(), prompt]
    resp = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="4:5"),
        ),
    )
    img_bytes = None
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            d = part.inline_data.data
            img_bytes = base64.b64decode(d) if isinstance(d, str) else d
            break
    if not img_bytes:
        print(f"  slide {idx}: no image returned, skipping"); return None

    base_path = SET_DIR / f"{idx:02d}_base.png"
    base_path.write_bytes(img_bytes)
    img = Image.open(base_path)
    final = overlay_text(img, lines)
    final_path = SET_DIR / f"{idx:02d}_final.png"
    final.save(final_path, "PNG")
    print(f"  slide {idx}: {final_path}")
    return final_path


def main():
    global REFS_DIR
    import argparse, random as _rnd
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=len(SLIDES))
    ap.add_argument("--style", default=None, help="folder name under styles/, or 'random'")
    args = ap.parse_args()

    if args.style is None or args.style == "random":
        choices = [p.name for p in STYLES_ROOT.iterdir() if p.is_dir()] if STYLES_ROOT.exists() else []
        style = _rnd.choice(choices) if choices else DEFAULT_STYLE
    else:
        style = args.style
    REFS_DIR = STYLES_ROOT / style
    if not REFS_DIR.exists():
        print(f"ERROR: style folder missing: {REFS_DIR}"); sys.exit(1)
    print(f"style: {style}  ({REFS_DIR})")
    print(f"Output dir: {SET_DIR}\n")

    for i, (scene, lines) in enumerate(SLIDES[: args.count], start=1):
        try:
            gen_one(i, scene, lines)
        except Exception as e:
            print(f"  slide {i} ERROR: {e}")
        time.sleep(1)
    print(f"\nDone. {SET_DIR}")


if __name__ == "__main__":
    main()
