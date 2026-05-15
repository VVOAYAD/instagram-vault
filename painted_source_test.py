"""Painted-source carousel generator (fallenpoe.t-style — light/dark/source narrative).
Generates all 7 slides for one carousel into output/test_slides/painted_source_<stamp>/.
Does NOT post anywhere. ~$0.14 per full carousel (Nano Banana 1).
"""
from __future__ import annotations
import base64, datetime as dt, os, sys, time
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).parent
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API = os.environ.get("GEMINI_API")
if not API:
    print("ERROR: GEMINI_API missing in .env"); sys.exit(1)

# --------- DNA — locked across every slide (palette swings per slide via SLIDES) ---------
DNA = (
    "MATCH THE PAINTED AESTHETIC of the reference images attached — same brushwork density, "
    "same canvas texture, same color depth, same figure stylization, same imperfection. "
    "These references are scanned poetry-book illustrations and contemporary painted figurative "
    "art (in the lineage of @thefallenpoe.t style). Treat them as ground truth for the visual "
    "style. Do NOT smooth, do NOT cleanly digitalize, do NOT render in glossy AI illustration "
    "style. The output must look like a real oil painting — visible thick brushstrokes, slightly "
    "clumsy figure proportions, raw canvas weave, varnish reflections, scanned-from-book quality, "
    "edges that aren't perfectly clean.\n\n"
    "Vertical 4:5 portrait. Figures are characters in a vignette — they tell a story. "
    "High saturation in the slide-specific palette, dramatic painterly mood. "
    "Painterly vignette edges. NO TEXT in the image — text is overlaid separately."
)

# --------- 7 slides — (scene_prompt_with_palette, [text_lines], text_color) ---------
# text_color: "white" for dark slides, "black" for bright/warm slides — fallenpoe.t convention
SLIDES = [
    # 1 — hook (without light, dark cannot exist)
    (
        "PALETTE: deep midnight blue dominant, with a single radiant candle gold as the only "
        "warm note. SCENE: a single candle burning in the center of a vast pitch-dark room. "
        "The dark is only legible because the flame reveals it. Nothing else in the frame — "
        "just the small flame and the dark it carves out around itself. Painterly, intimate, "
        "reverent, almost sacred.",
        ["WITHOUT LIGHT", "DARK CANNOT EXIST."],
        "white",
    ),
    # 2 — borrowed (the dark borrows from the light)
    (
        "PALETTE: deep teal and inky black dominant, with one bone-white luminous sphere and "
        "its hard cast shadow. SCENE: a luminous white sphere hovering in a vast dim hall, "
        "casting one long sharp shadow behind a still standing figure. The figure is barely "
        "visible — almost silhouette. The shadow is shaped by the light, not by the figure. "
        "Eerie, poetic, unsettling.",
        ["THE DARK BORROWS", "FROM THE LIGHT.", "THE LIGHT OWES NOTHING."],
        "white",
    ),
    # 3 — source (source does not fight the shadow)
    (
        "PALETTE: golden ochre and warm umber dominant, with amber sun pouring through. "
        "SCENE: a standing figure bathed in a single shaft of golden sun pouring through a "
        "tall high window into an old room. No fighting stance. Hands open at her sides. The "
        "light falls on her — she does not chase it, does not perform for it. Reverent, still, "
        "Sargent-like.",
        ["SOURCE DOES NOT", "FIGHT THE SHADOW.", "IT SIMPLY IS."],
        "black",
    ),
    # 4 — forgetting (when you forget you are light, the dark feels real)
    (
        "PALETTE: cool slate grey and black dominant, with faint candle warmth flickering at "
        "the edges. SCENE: a woman seated before a tall darkened antique mirror in a "
        "candlelit room. The mirror reflects only black — a void — she cannot see herself in "
        "it. Her own faint inner glow goes unseen by her. Melancholic, uncanny, lonely.",
        ["WHEN YOU FORGET", "YOU ARE LIGHT,", "THE DARK FEELS REAL."],
        "white",
    ),
    # 5 — return (presence is the return of source to itself)
    (
        "PALETTE: dawn lavender, rose gold, and pale cream dominant — soft, dreamlike. "
        "SCENE: a figure stepping into a vertical beam of soft pale light, eyes closed, face "
        "lifted, lips slightly parted. The moment of return. Hands relaxed at sides. "
        "Surrendered, unhurried, almost weightless. Hopper-quiet but luminous.",
        ["PRESENCE IS", "THE RETURN OF SOURCE", "TO ITSELF."],
        "black",
    ),
    # 6 — giving (source only gives)
    (
        "PALETTE: radiant gold, deep crimson, and warm amber dominant — sacred, almost "
        "biblical. SCENE: a radiant sun-disc above two open palms, pouring liquid gold light "
        "downward into them. The hands receive — they do not grasp, do not clench. The light "
        "has no agenda, asks for nothing. Thick painterly strokes, heavy canvas, glowing.",
        ["SOURCE ONLY GIVES.", "IT DOES NOT BARGAIN.", "IT DOES NOT WITHHOLD."],
        "black",
    ),
    # 7 — close (you were never broken, you were absent from yourself)
    (
        "PALETTE: dawn pale blue, soft gold, and cream dominant. SCENE: a woman waking on a "
        "couch under a tall window at dawn, soft golden light streaming across her face, eyes "
        "just opening. The room around her still held in shadow, but the light has already "
        "arrived. Tender, hopeful, the moment before she remembers everything.",
        ["YOU WERE NEVER BROKEN.", "YOU WERE ABSENT", "FROM YOURSELF.", "THE LIGHT WAITED."],
        "black",
    ),
]

stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
SET_DIR = ROOT / "output" / "test_slides" / f"painted_source_{stamp}"
SET_DIR.mkdir(parents=True, exist_ok=True)

client = genai.Client(api_key=API)

# Load painted style refs (fallenpoe.t-style scanned tiles) — fed to nano-banana as visual anchors
REFS_DIR = ROOT / "style_refs_painted"
def load_painted_refs() -> list[types.Part]:
    if not REFS_DIR.exists():
        return []
    parts = []
    for p in sorted(REFS_DIR.iterdir()):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            mime = "image/jpeg" if p.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
            parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    return parts

PAINTED_REFS = load_painted_refs()
print(f"Loaded {len(PAINTED_REFS)} painted style refs from {REFS_DIR}")

# Marker-style font fallback chain (Bradley Hand → Ink Free → Comic Sans Bold → Lucida)
FONT_CANDIDATES = [
    "C:/Windows/Fonts/BRADHITC.TTF",   # Bradley Hand ITC — closest to thick marker
    "C:/Windows/Fonts/Inkfree.ttf",    # Microsoft Ink Free — informal handwritten
    "C:/Windows/Fonts/comicbd.ttf",    # Comic Sans Bold — last-resort thick
    "C:/Windows/Fonts/LHANDW.TTF",     # Lucida Handwriting — thinnest fallback
]
FONT_PATH = next((p for p in FONT_CANDIDATES if Path(p).exists()), None)
if not FONT_PATH:
    print("ERROR: no usable handwritten font found"); sys.exit(1)
print(f"Using font: {FONT_PATH}")


def overlay_text(img: Image.Image, lines: list[str], color: str = "white") -> Image.Image:
    """Top-aligned ALL CAPS marker overlay. Sharp opposite-color outline for legibility on any palette."""
    img = img.convert("RGBA")
    W, H = img.size

    # Larger and bolder than the people-pleasing scaffold
    font_size = int(H * 0.055) if len(lines) <= 3 else int(H * 0.048)
    font = ImageFont.truetype(FONT_PATH, font_size)

    # Force ALL CAPS — the fallenpoe.t signature
    lines = [ln.upper() for ln in lines]

    if color == "black":
        fill = (15, 15, 15, 255)
        stroke = (255, 255, 255, 230)  # white halo behind black text
    else:
        fill = (250, 250, 250, 255)
        stroke = (0, 0, 0, 230)  # black halo behind white text

    text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    line_gap = int(font_size * 0.35)
    # Top-aligned: start text block at ~12% from top
    y = int(H * 0.12)

    stroke_w = max(3, int(font_size * 0.08))  # sharp outline, not soft glow
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_w)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        draw.text(
            (x, y), line, font=font, fill=fill,
            stroke_width=stroke_w, stroke_fill=stroke,
        )
        y += font_size + line_gap

    img = Image.alpha_composite(img, text_layer)
    return img.convert("RGB")


def gen_one(idx: int, scene: str, lines: list[str], color: str, out_dir: Path):
    prompt = f"{DNA}\n\n{scene}"
    print(f"[slide {idx}] generating...")
    contents: list = [*PAINTED_REFS, prompt] if PAINTED_REFS else [prompt]
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

    base_path = out_dir / f"{idx:02d}_base.png"
    base_path.write_bytes(img_bytes)
    img = Image.open(base_path)
    final = overlay_text(img, lines, color)
    final_path = out_dir / f"{idx:02d}_final.png"
    final.save(final_path, "PNG")
    print(f"  slide {idx}: {final_path}")
    return final_path


def rebake_one(idx: int, lines: list[str], color: str, src_dir: Path):
    """Re-overlay text on existing base PNG without calling the API."""
    base_path = src_dir / f"{idx:02d}_base.png"
    if not base_path.exists():
        print(f"  slide {idx}: missing {base_path}, skipping"); return None
    img = Image.open(base_path)
    final = overlay_text(img, lines, color)
    final_path = src_dir / f"{idx:02d}_final.png"
    final.save(final_path, "PNG")
    print(f"  slide {idx}: re-baked {final_path}")
    return final_path


# REBAKE_DIR=<dirname under output/test_slides/> → skip generation, just re-overlay text
rebake_dir_name = os.environ.get("REBAKE_DIR")
if rebake_dir_name:
    src_dir = ROOT / "output" / "test_slides" / rebake_dir_name
    print(f"REBAKE mode — re-overlaying text on bases in: {src_dir}\n")
    for i, (_, lines, color) in enumerate(SLIDES, start=1):
        try:
            rebake_one(i, lines, color, src_dir)
        except Exception as e:
            print(f"  slide {i} ERROR: {e}")
    print(f"\nDone. {src_dir}")
else:
    print(f"Output dir: {SET_DIR}\n")
    for i, (scene, lines, color) in enumerate(SLIDES, start=1):
        try:
            gen_one(i, scene, lines, color, SET_DIR)
        except Exception as e:
            print(f"  slide {i} ERROR: {e}")
        time.sleep(1)
    print(f"\nDone. {SET_DIR}")
