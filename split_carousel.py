"""Split-panel carousel generator — fallenpoet DNA.
Each slide = 4:5 vertical image, vertically split into TWO illustrated halves
contrasting two concepts. ALL-CAPS Bebas Neue text overlaid on each half.
Slide 1 is a single-image cover slide with the topic title.

Usage:
  python split_carousel.py --style fallenpoet --count 2
"""
from __future__ import annotations
import argparse, base64, datetime as dt, os, random, sys, textwrap, time
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
STYLES_ROOT = ROOT / "styles"
DEFAULT_STYLE = "fallenpoet"

env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API = os.environ.get("GEMINI_API")
if not API:
    print("ERROR: GEMINI_API missing"); sys.exit(1)

CAPS_FONT = str(ROOT / "fonts" / "BebasNeue-Regular.ttf")
IMAGE_MODEL = "gemini-3-pro-image-preview"  # Nano Banana Pro — highest fidelity

DNA = (
    "RAW painterly oil painting on rough canvas — clearly the work of a human painter, not digital "
    "illustration. Thick visible impasto brushstrokes, palette-knife marks, exposed canvas weave, "
    "imperfect uneven edges, paint drips, slightly off-anatomy figures — beautifully unpolished. "
    "In the style of Edward Hopper, Lucian Freud, Felix Vallotton, Edvard Munch, and contemporary "
    "painters like Jenny Saville and Howard Hodgkin. Saturated but moody palette — deep teal, "
    "burnt sienna, oxblood, mustard, indigo, ochre. Cinematic shadow, single dominant light source, "
    "dusk or candle-lit interiors. Simplified poster-like composition. "
    "Match the texture, brushwork, and emotional weight of the reference images. "
    "HUMANIZE THE FIGURE: specific imperfect humans with lived-in faces — asymmetric features, "
    "tired eyes, real skin with light wrinkles or freckles, particular weight and posture, "
    "awkward authentic body language. Not a model. Not idealized. Specific real person caught "
    "in a real moment. Off-center composition, cropped close, slightly tense framing. "
    "ABSOLUTELY NOT: digital art, 3D render, commercial illustration, stock photography, "
    "Pixar/Disney style, AI-glossy, smooth gradients, perfect symmetric anatomy, instagram-pretty, "
    "default-pretty-young-woman, generic faces, centered subject. "
    "This must look like a real painting hung in a gallery, not a digital asset. "
    "NO TEXT in the image."
)

# topic + slides — plain English, no clinical jargon
TOPIC = "EVERYONE'S SAFE PLACE"
TOPIC_SUB = "and the price you're paying for the title"

# Each slide: ("cover" | "split", left_data, right_data)
# cover: ("cover", scene_prompt, None)
# split: ("split", (left_caption, left_scene), (right_caption, right_scene))
SLIDES = [
    (
        "cover",
        ("A solitary young woman seated alone on a worn velvet couch in a dim candlelit room, "
         "knees pulled up, head bowed slightly. Heavy curtains, antique wallpaper, a single candle "
         "casting amber glow. Quiet, intimate, melancholic."),
        None,
    ),
    (
        "split",
        ("WHO STAYS WHEN YOU'RE STURDY",
         "A young woman seated upright at a busy table, calmly serving food to several blurred "
         "guests around her, all of them turned toward her, smiling, leaning in. Warm candlelight, "
         "crowded scene, she is the center."),
        ("WHO STAYS WHEN YOU REST",
         "The same young woman asleep alone on a couch in soft afternoon light, blanket half over her. "
         "In the background, blurred figures stand near a doorway with their coats, half-turned to leave. "
         "The room feels emptier. Quiet, muted."),
    ),
]


def load_refs(style: str) -> list[types.Part]:
    folder = STYLES_ROOT / style
    if not folder.exists():
        return []
    parts = []
    for p in sorted(folder.iterdir()):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            mime = "image/jpeg" if p.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
            parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    return parts


def gen_image(client, refs, prompt: str) -> Image.Image:
    contents = [*refs, f"{DNA}\n\nScene: {prompt}"]
    resp = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="4:5"),
        ),
    )
    for part in resp.candidates[0].content.parts:
        d = getattr(part, "inline_data", None) and part.inline_data.data
        if d:
            data = base64.b64decode(d) if isinstance(d, str) else d
            tmp = ROOT / "_tmp_gen.png"
            tmp.write_bytes(data)
            img = Image.open(tmp).convert("RGB")
            tmp.unlink(missing_ok=True)
            return img
    raise RuntimeError("no image returned")


def stitch_split(left: Image.Image, right: Image.Image) -> Image.Image:
    """Stitch two 4:5 images into one 4:5 canvas (each becomes a 2:5 column)."""
    target_h = 1500
    target_w = int(target_h * 4 / 5)  # 1200
    half_w = target_w // 2
    out = Image.new("RGB", (target_w, target_h), (0, 0, 0))
    for i, src in enumerate((left, right)):
        # crop the center vertical strip from each source
        sw, sh = src.size
        # we want a slice that is half_w wide at full height
        scale = target_h / sh
        new_w = int(sw * scale)
        resized = src.resize((new_w, target_h), Image.LANCZOS)
        crop_x = (new_w - half_w) // 2
        slice_ = resized.crop((crop_x, 0, crop_x + half_w, target_h))
        out.paste(slice_, (i * half_w, 0))
    # subtle divider
    draw = ImageDraw.Draw(out)
    draw.line([(half_w, 0), (half_w, target_h)], fill=(0, 0, 0), width=2)
    return out


def overlay_caps(img: Image.Image, caption: str, position: str = "bottom",
                 column: str | None = None) -> Image.Image:
    """Overlay ALL-CAPS Bebas text. position=top|bottom; column=left|right|None (full width)."""
    img = img.convert("RGBA")
    W, H = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if column == "left":
        x_start, x_end = int(W * 0.04), int(W * 0.50) - 12
    elif column == "right":
        x_start, x_end = int(W * 0.50) + 12, int(W * 0.96)
    else:
        x_start, x_end = int(W * 0.06), int(W * 0.94)
    box_w = x_end - x_start

    # find a font size that fits
    text = caption.upper()
    size = int(H * 0.05) if column else int(H * 0.07)
    font = ImageFont.truetype(CAPS_FONT, size)
    # rough wrap
    avg_char = font.getbbox("M")[2] * 0.65
    chars_per_line = max(8, int(box_w / avg_char))
    lines = textwrap.wrap(text, width=chars_per_line)
    line_h = font.getbbox("Mg")[3] + 6
    total_h = line_h * len(lines)

    if position == "top":
        y = int(H * 0.05)
    else:
        y = H - total_h - int(H * 0.05)

    # dark gradient backdrop strip for legibility
    pad_y = int(H * 0.02)
    backdrop = (0, 0, 0, 130)
    draw.rectangle([(x_start - 6, y - pad_y), (x_end + 6, y + total_h + pad_y)], fill=backdrop)

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = x_start + (box_w - line_w) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_h

    return Image.alpha_composite(img, layer).convert("RGB")


def build_cover(client, refs, scene: str, title: str, subtitle: str) -> Image.Image:
    base = gen_image(client, refs, scene)
    img = overlay_caps(base, title, position="bottom")
    img = overlay_caps(img, subtitle, position="top")
    return img


def build_split(client, refs, left_cap: str, left_scene: str, right_cap: str, right_scene: str) -> Image.Image:
    left = gen_image(client, refs, left_scene)
    right = gen_image(client, refs, right_scene)
    stitched = stitch_split(left, right)
    stitched = overlay_caps(stitched, left_cap, position="bottom", column="left")
    stitched = overlay_caps(stitched, right_cap, position="bottom", column="right")
    return stitched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", default=DEFAULT_STYLE)
    ap.add_argument("--count", type=int, default=len(SLIDES))
    args = ap.parse_args()

    refs = load_refs(args.style)
    print(f"style: {args.style} ({len(refs)} refs)")
    today = dt.datetime.now().strftime("%Y-%m-%d")
    out_dir = ROOT / "output" / today
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"output: {out_dir}\n")

    client = genai.Client(api_key=API)

    for i, slide in enumerate(SLIDES[: args.count], start=1):
        kind = slide[0]
        print(f"[slide {i}] {kind}")
        try:
            if kind == "cover":
                img = build_cover(client, refs, slide[1], TOPIC, TOPIC_SUB)
            else:
                (lc, ls), (rc, rs) = slide[1], slide[2]
                img = build_split(client, refs, lc, ls, rc, rs)
            path = out_dir / f"split_{i:02d}.png"
            img.save(path)
            print(f"  -> {path}")
        except Exception as e:
            print(f"  ERROR: {e}")
        time.sleep(1)


if __name__ == "__main__":
    main()
