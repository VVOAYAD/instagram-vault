"""
Builds all 7 carousel slides as 1080x1080 JPEG images.

Slide structure:
  1 — Hook (AI-generated background + hook text overlay)
  2-6 — Content slides (dark bg, one thought per slide)
  7 — CTA (save/share prompt + handle)
"""

import io
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1080

# ── Fonts ─────────────────────────────────────────────────────────────────

_SERIF = [
    "C:/Windows/Fonts/georgia.ttf",
    "C:/Windows/Fonts/Georgia.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_ITALIC = [
    "C:/Windows/Fonts/georgiai.ttf",
    "C:/Windows/Fonts/timesi.ttf",
    "C:/Windows/Fonts/ariali.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_cache: dict = {}


def _font(size: int, italic: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, italic)
    if key in _cache:
        return _cache[key]
    for path in (_ITALIC if italic else _SERIF):
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size)
                _cache[key] = f
                return f
            except Exception:
                continue
    try:
        f = ImageFont.load_default(size=size)
    except TypeError:
        f = ImageFont.load_default()
    _cache[key] = f
    return f


# ── Color helpers ─────────────────────────────────────────────────────────

def _rgb(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    return tuple(int(h[i: i + 2], 16) for i in (0, 2, 4))


def _rgba(hex_str: str, alpha: int) -> tuple:
    return (*_rgb(hex_str), alpha)


# ── Text helpers ──────────────────────────────────────────────────────────

def _tw(draw: ImageDraw.Draw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _wrap(text: str, font, draw: ImageDraw.Draw, max_px: int) -> list:
    """Word-wrap text so each line fits within max_px."""
    words = text.split()
    result, current = [], []
    for word in words:
        test = " ".join(current + [word])
        if _tw(draw, test, font) <= max_px:
            current.append(word)
        else:
            if current:
                result.append(" ".join(current))
            current = [word]
    if current:
        result.append(" ".join(current))
    return result or [""]


# ── Shared UI elements ────────────────────────────────────────────────────

def _slide_number(draw: ImageDraw.Draw, n: int, total: int, accent: str):
    label = f"{n}  /  {total}"
    font = _font(22, italic=True)
    w = _tw(draw, label, font)
    draw.text((W - 56 - w, 50), label, font=font, fill=_rgba(accent, 130))


def _swipe_arrow(draw: ImageDraw.Draw, accent: str):
    font = _font(28, italic=True)
    draw.text((W - 64, H - 70), "→", font=font, fill=_rgba(accent, 150))


def _accent_line(img: Image.Image, cx: int, y: int, half_w: int, accent: str, alpha: int = 150):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.line([(cx - half_w, y), (cx + half_w, y)], fill=_rgba(accent, alpha), width=1)
    img.paste(ov, mask=ov)


# ── Slide 1 — Hook ────────────────────────────────────────────────────────

def slide_hook(hook_text: str, bg_bytes: bytes, config: dict) -> Image.Image:
    """Slide 1: AI background + dark gradient + hook text."""
    accent = config.get("image_style", {}).get("accent_color", "#9B7D52")
    text_color = _rgb(config.get("image_style", {}).get("text_color", "#F0EBE0"))

    # Background: crop to square, resize to 1080
    bg = Image.open(io.BytesIO(bg_bytes)).convert("RGB")
    bw, bh = bg.size
    s = min(bw, bh)
    bg = bg.crop(((bw - s) // 2, (bh - s) // 2, (bw + s) // 2, (bh + s) // 2))
    bg = bg.resize((W, H), Image.LANCZOS)

    # Dark veil over whole image
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 55))
    bg = bg.convert("RGBA")
    bg.paste(veil, mask=veil)

    # Gradient — transparent top → opaque bottom
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    start = int(H * 0.30)
    for y in range(start, H):
        t = (y - start) / (H - start)
        a = int(min(1.0, t * 1.5) * 220)
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    bg.paste(grad, mask=grad)
    bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)
    _slide_number(draw, 1, 7, accent)
    _swipe_arrow(draw, accent)

    # Hook text — lower third
    max_w = W - 120
    for fs in (70, 60, 52, 44, 38):
        font = _font(fs)
        lines = _wrap(hook_text, font, draw, max_w)
        lh = int(fs * 1.38)
        if len(lines) * lh < H * 0.38:
            break

    total_h = len(lines) * lh
    y0 = int(H * 0.57)

    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))  # shadow
        draw.text((x, y), line, font=font, fill=text_color)

    return bg


# ── Slides 2-6 — Content ─────────────────────────────────────────────────

def slide_content(n: int, text: str, eyebrow: str, config: dict) -> Image.Image:
    bg_color = _rgb(config.get("image_style", {}).get("background", "#0D0D0D"))
    text_color = config.get("image_style", {}).get("text_color", "#F0EBE0")
    accent = config.get("image_style", {}).get("accent_color", "#9B7D52")

    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    _slide_number(draw, n, 7, accent)
    if n < 7:
        _swipe_arrow(draw, accent)

    # Font size based on text length
    nc = len(text)
    if nc < 80:
        fs, max_w = 52, W - 140
    elif nc < 160:
        fs, max_w = 44, W - 120
    elif nc < 260:
        fs, max_w = 36, W - 120
    else:
        fs, max_w = 30, W - 100

    font = _font(fs)
    lh = int(fs * 1.48)
    lines = _wrap(text, font, draw, max_w)
    text_h = len(lines) * lh

    eb_font = _font(22, italic=True)
    eb_h = 44 if eyebrow.strip() else 0
    gap = 20
    block = eb_h + (gap if eyebrow.strip() else 0) + text_h
    y0 = (H - block) // 2

    # Accent line above
    _accent_line(img, W // 2, y0 - 30, 52, accent)

    # Eyebrow
    if eyebrow.strip():
        label = eyebrow.strip().upper()
        ew = _tw(draw, label, eb_font)
        draw.text(((W - ew) // 2, y0), label, font=eb_font, fill=_rgba(accent, 190))

    # Main text
    ty = y0 + eb_h + (gap if eyebrow.strip() else 0)
    for i, line in enumerate(lines):
        y = ty + i * lh
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x, y), line, font=font, fill=_rgb(text_color))

    # Accent line below
    _accent_line(img, W // 2, ty + text_h + 24, 52, accent)

    return img


# ── Slide 7 — CTA ────────────────────────────────────────────────────────

def slide_cta(cta_text: str, config: dict) -> Image.Image:
    bg_color = _rgb(config.get("image_style", {}).get("background", "#0D0D0D"))
    text_color = config.get("image_style", {}).get("text_color", "#F0EBE0")
    accent = config.get("image_style", {}).get("accent_color", "#9B7D52")
    handle = config.get("instagram_handle", "")

    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)
    _slide_number(draw, 7, 7, accent)

    cta_font = _font(50)
    handle_font = _font(28, italic=True)
    lh = int(50 * 1.42)

    lines = _wrap(cta_text, cta_font, draw, W - 160)
    cta_h = len(lines) * lh
    divider_gap = 36
    handle_h = 50 if handle else 0
    block = cta_h + divider_gap + handle_h
    y0 = (H - block) // 2

    _accent_line(img, W // 2, y0 - 32, 50, accent)

    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, cta_font)) // 2
        draw.text((x, y), line, font=cta_font, fill=_rgb(text_color))

    _accent_line(img, W // 2, y0 + cta_h + divider_gap // 2, 40, accent, alpha=110)

    if handle:
        hw = _tw(draw, handle, handle_font)
        draw.text(((W - hw) // 2, y0 + cta_h + divider_gap), handle, font=handle_font, fill=_rgba(accent, 200))

    return img


# ── Main builder ──────────────────────────────────────────────────────────

def build_carousel(slides: dict, bg_bytes: bytes, config: dict, out_dir: Path) -> list:
    """
    Build all 7 slides and save to out_dir.
    slides keys: slide_1_hook, slide_2..6 (each has 'text', 'eyebrow'), slide_7_cta
    Returns list of Path objects.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    print("  Building slides...")

    # 1 — Hook
    img = slide_hook(slides["slide_1_hook"], bg_bytes, config)
    p = out_dir / "slide_01.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print(f"    ✓ Slide 1 (hook)")

    # 2-6 — Content
    for n in range(2, 7):
        data = slides.get(f"slide_{n}", {})
        img = slide_content(n, data.get("text", ""), data.get("eyebrow", ""), config)
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n}")

    # 7 — CTA
    img = slide_cta(slides["slide_7_cta"], config)
    p = out_dir / "slide_07.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print(f"    ✓ Slide 7 (CTA)")

    return paths
