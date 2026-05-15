"""Painted-lane slide tester (fallenpoe-style).
1) Generate clean image (no text) via Nano Banana at 4:5
2) Overlay handwritten serif text via PIL with soft glow
Output to output/test_slides/. Does NOT post anywhere.
"""
from __future__ import annotations
import base64, datetime as dt, os, sys
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).parent
OUT = ROOT / "output" / "test_slides"
OUT.mkdir(parents=True, exist_ok=True)

env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API = os.environ.get("GEMINI_API")
if not API:
    print("ERROR: GEMINI_API missing in .env"); sys.exit(1)

# Visual prompt — NO text instruction (we overlay separately)
PROMPT = (
    "Vertical 4:5 portrait, romantic classical oil painting in the style of John Singer Sargent "
    "and Andrew Wyeth. Foreground close-up: a pair of feminine hands and forearms, sleeves rolled "
    "to the elbow, pouring a steaming pot of tea into four porcelain cups arranged on a wooden "
    "tray. Her face and body are NOT shown — only the hands and forearms. Background: a long dim "
    "candlelit dining room, four blurred guests seated around a dark wooden table, all turned "
    "toward each other deep in conversation, none looking at the hands serving them. Candles "
    "between them, warm soft bokeh. Palette: deep umber, ochre, gold, cool teal-grey shadows. "
    "Thick visible oil brushstrokes, heavy canvas grain, dramatic chiaroscuro, painterly vignette "
    "edges, dreamy melancholic poetry-book illustration atmosphere. NO TEXT in the image."
)

TEXT_LINES = ["they miss your function.", "not your presence."]

# ---------- 1. generate base image ----------
print("[1/2] Generating base image (4:5, no text)...")
client = genai.Client(api_key=API)
resp = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[PROMPT],
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
    print("No image returned."); sys.exit(1)

stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
base_path = OUT / f"slide5_base_{stamp}.png"
base_path.write_bytes(img_bytes)
print(f"  base saved: {base_path}")

# ---------- 2. overlay handwritten text ----------
print("[2/2] Overlaying handwritten text...")
img = Image.open(base_path).convert("RGBA")
W, H = img.size

# Try Lucida Handwriting (handwritten, included on Windows)
FONT_PATH = "C:/Windows/Fonts/LHANDW.TTF"
font_size = int(H * 0.045)  # ~4.5% of height per line
try:
    font = ImageFont.truetype(FONT_PATH, font_size)
except Exception as e:
    print(f"  font fallback (no LHANDW): {e}")
    font = ImageFont.load_default()

# Compose text on transparent layer with soft glow
text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(text_layer)

# Measure & position lower-center
line_gap = int(font_size * 0.4)
total_h = len(TEXT_LINES) * font_size + (len(TEXT_LINES) - 1) * line_gap
y = int(H * 0.78) - total_h // 2  # lower third

for line in TEXT_LINES:
    bbox = draw.textbbox((0, 0), line, font=font)
    line_w = bbox[2] - bbox[0]
    x = (W - line_w) // 2
    draw.text((x, y), line, font=font, fill=(255, 255, 255, 240))
    y += font_size + line_gap

# Soft glow: blurred copy underneath
glow = text_layer.filter(ImageFilter.GaussianBlur(radius=int(font_size * 0.25)))
img = Image.alpha_composite(img, glow)
img = Image.alpha_composite(img, text_layer)

final_path = OUT / f"slide5_final_{stamp}.png"
img.convert("RGB").save(final_path, "PNG")
print(f"  final saved: {final_path}")
print(f"  size: {W}x{H}")
