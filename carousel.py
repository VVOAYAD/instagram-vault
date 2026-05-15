"""7-slide carousel generator with text baked in.
Loads style refs + slide texts, generates 7 images.
Output: Desktop/instagram system samples/<post>/01.png .. 07.png

Usage:
  python carousel.py --style retro_futurism --post 1
  python carousel.py --style retro_futurism --post 1 --model gemini-3.1-flash-image-preview
"""
from __future__ import annotations
import argparse, base64, json, os, sys, time
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).parent
STYLES_ROOT = ROOT / "styles"
OUT_ROOT = Path(r"C:\Users\Administrator\Desktop\instagram system samples")
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"  # NB2 — Alvvo's pick

env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API = os.environ.get("GEMINI_API")
if not API:
    print("ERROR: GEMINI_API missing in .env"); sys.exit(1)

# 7 slides — emotional maturity, Alvvo's voice (NOTICER tone)
SLIDES = [
    {
        "role": "cover",
        "text": "EMOTIONAL MATURITY ISN'T WHAT THEY TOLD YOU IT WAS",
        "scene": "a single human figure paused mid-step, caught between motion and stillness",
    },
    {
        "role": "body",
        "text": "They told us mature meant calm. Quiet. Polite.\nBut the polite version of you is usually the one most afraid of what you're feeling.",
        "scene": "a face holding back, lips closed, eyes carrying a storm — quiet outside, electric inside",
    },
    {
        "role": "body",
        "text": "Real maturity is the war you win in silence.\nThe same input hits — you choose a different output.",
        "scene": "a body still in the eye of a storm, energy swirling around but not touching",
    },
    {
        "role": "body",
        "text": "It's not about feeling less.\nIt's about not letting the feeling write the response.",
        "scene": "two versions of the same figure — one reactive, one centered — both inside one frame",
    },
    {
        "role": "body",
        "text": "People will pull you to react.\nThat's the trap. You don't have to shut down.\nYou just stop leaking.",
        "scene": "a sealed glowing figure, surrounded by hands reaching, but nothing flows out",
    },
    {
        "role": "body",
        "text": "The threat usually isn't now.\nIt's a memory your nervous system never filed away.",
        "scene": "a present-day room overlaid with a ghost of an old scene, two timelines bleeding into one",
    },
    {
        "role": "close",
        "text": "Mature isn't soft.\nIt isn't loud.\nIt's staying full when everyone wants you to spill.",
        "scene": "a luminous full vessel — chrome, intact, glowing at the center of an empty room",
    },
]

DNA_BASE = (
    "Vertical 4:5 image. Match the visual style of the reference images EXACTLY — "
    "same palette, texture, rendering technique, composition language, mood, overall feel. "
    "The refs are the source of truth for the aesthetic. "
)

TYPO_RULE = (
    "BAKE THE TEXT INTO THE IMAGE in bold ALL-CAPS Y2K poster typography that fits the "
    "retro/chrome aesthetic of the refs — sharp, punchy, integrated into the composition. "
    "Render the text EXACTLY as written below, character-for-character, no spelling errors, "
    "no extra words, no extra letters, no decorative changes. "
    "Place text legibly with strong contrast. "
    "IMPORTANT Instagram safe zones: keep text out of the TOP 15% and BOTTOM 25% of the image "
    "(those areas are covered by Instagram UI). Text belongs in the middle vertical band. "
    "TEXT TO RENDER (render exactly):\n{text}"
)

FONT_PATH = str(ROOT / "fonts" / "BebasNeue-Regular.ttf")


def _wrap_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Greedy word-wrap a single string to a max pixel width."""
    words = text.split()
    if not words:
        return []
    lines, cur = [], words[0]
    for w in words[1:]:
        trial = f"{cur} {w}"
        bw = draw.textbbox((0, 0), trial, font=font)[2]
        if bw <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def overlay_text(img_bytes: bytes, text: str) -> bytes:
    """Overlay ALL-CAPS text in the IG-safe middle band. Auto-wraps + auto-shrinks."""
    from io import BytesIO
    img = Image.open(BytesIO(img_bytes)).convert("RGBA")
    W, H = img.size
    # IG safe zones: top 18% (header), bottom 28% (action buttons + caption)
    safe_top = int(H * 0.18)
    safe_bottom = int(H * 0.72)
    safe_h = safe_bottom - safe_top
    # Horizontal margin: 8% each side
    margin_x = int(W * 0.08)
    text_w = W - 2 * margin_x

    paragraphs = [p.strip().upper() for p in text.split("\n") if p.strip()]

    # Find largest font where (a) every paragraph wraps within text_w, (b) total height fits safe_h
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    chosen_size = int(W * 0.085)
    chosen_lines: list[str] = []
    while chosen_size >= int(W * 0.035):
        font = ImageFont.truetype(FONT_PATH, chosen_size)
        lines: list[str] = []
        ok = True
        for p in paragraphs:
            wrapped = _wrap_to_width(p, font, text_w, draw)
            for w_line in wrapped:
                if draw.textbbox((0, 0), w_line, font=font)[2] > text_w:
                    ok = False
                    break
            if not ok:
                break
            lines.extend(wrapped)
        if ok:
            line_gap = int(chosen_size * 0.18)
            n = len(lines)
            total_h = n * chosen_size + (n - 1) * line_gap
            if total_h <= safe_h:
                chosen_lines = lines
                break
        chosen_size -= 4
    if not chosen_lines:
        font = ImageFont.truetype(FONT_PATH, chosen_size)
        chosen_lines = []
        for p in paragraphs:
            chosen_lines.extend(_wrap_to_width(p, font, text_w, draw))

    font = ImageFont.truetype(FONT_PATH, chosen_size)
    line_gap = int(chosen_size * 0.18)
    n = len(chosen_lines)
    total_h = n * chosen_size + (n - 1) * line_gap
    y = safe_top + max(0, (safe_h - total_h) // 2)

    shadow_offsets = [(-4, 4), (4, 4), (-4, -4), (4, -4), (0, 5), (0, -5)]
    for line in chosen_lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        for dx, dy in shadow_offsets:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 200))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += chosen_size + line_gap

    glow = layer.filter(ImageFilter.GaussianBlur(radius=int(chosen_size * 0.18)))
    composed = Image.alpha_composite(img, glow)
    composed = Image.alpha_composite(composed, layer)
    out = BytesIO()
    composed.convert("RGB").save(out, "PNG")
    return out.getvalue()


def load_refs(style: str) -> list[types.Part]:
    folder = STYLES_ROOT / style
    if not folder.exists():
        print(f"ERROR: style folder missing: {folder}"); sys.exit(1)
    imgs = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    parts = []
    for p in imgs:
        mime = "image/jpeg" if p.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    print(f"  loaded {len(parts)} refs from styles/{style}/")
    return parts


def gen_one(client, refs, model: str, slide: dict) -> bytes | None:
    prompt = (
        DNA_BASE
        + f"\n\nScene: {slide['scene']}.\n\n"
        + TYPO_RULE.format(text=slide["text"])
    )
    contents = [*refs, prompt]
    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="4:5"),
        ),
    )
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                d = inline.data
                return base64.b64decode(d) if isinstance(d, str) else d
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", required=True)
    ap.add_argument("--post", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    out = OUT_ROOT / str(args.post)
    out.mkdir(parents=True, exist_ok=True)
    print(f"style: {args.style}  |  post: {args.post}  |  model: {args.model}")
    print(f"out:   {out}\n")

    client = genai.Client(api_key=API)
    refs = load_refs(args.style)

    # save the slide plan for traceability
    (out / "slide_plan.json").write_text(json.dumps(SLIDES, indent=2), encoding="utf-8")

    for i, slide in enumerate(SLIDES, start=1):
        print(f"[slide {i}/{len(SLIDES)}] {slide['role']:5s} -> {slide['text'][:60]}...")
        try:
            data = gen_one(client, refs, args.model, slide)
        except Exception as e:
            print(f"  ERROR: {e}"); continue
        if not data:
            print(f"  no image returned"); continue
        path = out / f"{i:02d}.png"
        path.write_bytes(data)
        print(f"  -> {path.name}")
        time.sleep(1)

    print(f"\n[done] {out}")


if __name__ == "__main__":
    main()
