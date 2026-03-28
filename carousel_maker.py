"""
Builds all 7 carousel slides as 1080x1080 JPEG images.

Three patterns:
  gap            — The Gap: dark bg, serif text, gold accents (original)
  cosmic_duality — The Cosmic Duality: single words on AI bg, neon glow
  vibrational_anchor — The Vibrational Anchor: gradient bg, bold white text
"""

import io
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
_BOLD = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_cache: dict = {}


def _font(size: int, italic: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, italic, bold)
    if key in _cache:
        return _cache[key]
    paths = _BOLD if bold else (_ITALIC if italic else _SERIF)
    for path in paths:
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


def _th(draw: ImageDraw.Draw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def _wrap(text: str, font, draw: ImageDraw.Draw, max_px: int) -> list:
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


def _crop_bg(bg_bytes: bytes) -> Image.Image:
    """Load image bytes, crop to square, resize to 1080."""
    bg = Image.open(io.BytesIO(bg_bytes)).convert("RGB")
    bw, bh = bg.size
    s = min(bw, bh)
    bg = bg.crop(((bw - s) // 2, (bh - s) // 2, (bw + s) // 2, (bh + s) // 2))
    return bg.resize((W, H), Image.LANCZOS)


# ── Pattern 0: The Gap ────────────────────────────────────────────────────

def slide_hook(hook_text: str, bg_bytes: bytes, config: dict) -> Image.Image:
    """Slide 1: AI background + dark gradient + hook text."""
    accent = config.get("image_style", {}).get("accent_color", "#9B7D52")
    text_color = _rgb(config.get("image_style", {}).get("text_color", "#F0EBE0"))

    bg = _crop_bg(bg_bytes)

    veil = Image.new("RGBA", (W, H), (0, 0, 0, 55))
    bg = bg.convert("RGBA")
    bg.paste(veil, mask=veil)

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

    max_w = W - 120
    for fs in (70, 60, 52, 44, 38):
        font = _font(fs)
        lines = _wrap(hook_text, font, draw, max_w)
        lh = int(fs * 1.38)
        if len(lines) * lh < H * 0.38:
            break

    lh = int(fs * 1.38)
    y0 = int(H * 0.57)
    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=text_color)

    return bg


def slide_content(n: int, text: str, eyebrow: str, config: dict) -> Image.Image:
    bg_color = _rgb(config.get("image_style", {}).get("background", "#0D0D0D"))
    text_color = config.get("image_style", {}).get("text_color", "#F0EBE0")
    accent = config.get("image_style", {}).get("accent_color", "#9B7D52")

    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    _slide_number(draw, n, 7, accent)
    if n < 7:
        _swipe_arrow(draw, accent)

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

    _accent_line(img, W // 2, y0 - 30, 52, accent)

    if eyebrow.strip():
        label = eyebrow.strip().upper()
        ew = _tw(draw, label, eb_font)
        draw.text(((W - ew) // 2, y0), label, font=eb_font, fill=_rgba(accent, 190))

    ty = y0 + eb_h + (gap if eyebrow.strip() else 0)
    for i, line in enumerate(lines):
        y = ty + i * lh
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x, y), line, font=font, fill=_rgb(text_color))

    _accent_line(img, W // 2, ty + text_h + 24, 52, accent)

    return img


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
        draw.text(((W - hw) // 2, y0 + cta_h + divider_gap), handle,
                  font=handle_font, fill=_rgba(accent, 200))

    return img


def build_carousel_gap(slides: dict, bg_bytes: bytes, config: dict, out_dir: Path) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    print("  Building slides (Pattern: The Gap)...")

    img = slide_hook(slides["slide_1_hook"], bg_bytes, config)
    p = out_dir / "slide_01.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 1 (hook)")

    for n in range(2, 7):
        data = slides.get(f"slide_{n}", {})
        img = slide_content(n, data.get("text", ""), data.get("eyebrow", ""), config)
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n}")

    img = slide_cta(slides["slide_7_cta"], config)
    p = out_dir / "slide_07.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 7 (CTA)")

    return paths


# ── Pattern 1: The Cosmic Duality ─────────────────────────────────────────

_COSMIC_ACCENTS = ["#7C3AED", "#0EA5E9", "#14B8A6", "#8B5CF6", "#06B6D4"]


def slide_cosmic_word(n: int, word: str, bg_bytes: bytes, config: dict) -> Image.Image:
    """Single large word on AI background with neon glow."""
    bg = _crop_bg(bg_bytes)

    veil = Image.new("RGBA", (W, H), (0, 0, 0, 170))
    bg = bg.convert("RGBA")
    bg.paste(veil, mask=veil)

    accent_hex = _COSMIC_ACCENTS[(n - 1) % len(_COSMIC_ACCENTS)]
    tint = Image.new("RGBA", (W, H), (*_rgb(accent_hex), 25))
    bg.paste(tint, mask=tint)
    bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)
    _slide_number(draw, n, 7, accent_hex)
    _swipe_arrow(draw, accent_hex)

    # Scale font to fit
    fs = 200
    font = _font(fs, italic=True)
    while _tw(draw, word, font) > W - 80 and fs > 60:
        fs -= 10
        font = _font(fs, italic=True)

    word_w = _tw(draw, word, font)
    word_h = _th(draw, word, font)
    x = (W - word_w) // 2
    y = (H - word_h) // 2

    # Neon glow behind text
    glow_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_ov)
    pad = 50
    gd.rectangle([x - pad, y - pad, x + word_w + pad, y + word_h + pad],
                 fill=(*_rgb(accent_hex), 70))
    glow_ov = glow_ov.filter(ImageFilter.GaussianBlur(40))
    bg = bg.convert("RGBA")
    bg.paste(glow_ov, mask=glow_ov)
    bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)
    draw.text((x + 3, y + 3), word, font=font, fill=(0, 0, 0))
    draw.text((x, y), word, font=font, fill=_rgb("#F0EBE0"))

    return bg


def slide_cosmic_reveal(n: int, text: str, bg_bytes: bytes, config: dict) -> Image.Image:
    """Full revelation sentence on AI background."""
    bg = _crop_bg(bg_bytes)

    veil = Image.new("RGBA", (W, H), (0, 0, 0, 140))
    bg = bg.convert("RGBA")
    bg.paste(veil, mask=veil)
    bg = bg.convert("RGB")

    accent_hex = "#C4A97D"
    draw = ImageDraw.Draw(bg)
    _slide_number(draw, n, 7, accent_hex)
    if n < 7:
        _swipe_arrow(draw, accent_hex)

    max_w = W - 120
    for fs in (80, 68, 56, 46, 38):
        font = _font(fs, italic=True)
        lines = _wrap(text, font, draw, max_w)
        lh = int(fs * 1.38)
        if len(lines) * lh < H * 0.5:
            break

    lh = int(fs * 1.38)
    total_h = len(lines) * lh
    y0 = (H - total_h) // 2

    _accent_line(bg, W // 2, y0 - 36, 90, accent_hex)

    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=_rgb("#F0EBE0"))

    _accent_line(bg, W // 2, y0 + total_h + 28, 90, accent_hex)

    return bg


def build_carousel_cosmic(slides: dict, bg_bytes: bytes, config: dict, out_dir: Path) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    print("  Building slides (Pattern: Cosmic Duality)...")

    for n in range(1, 5):
        word = slides.get(f"slide_{n}_word", "")
        img = slide_cosmic_word(n, word, bg_bytes, config)
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n} ({word})")

    img = slide_cosmic_reveal(5, slides.get("slide_5_revelation", ""), bg_bytes, config)
    p = out_dir / "slide_05.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 5 (revelation)")

    data = slides.get("slide_6", {})
    img = slide_content(6, data.get("text", ""), data.get("eyebrow", ""), config)
    p = out_dir / "slide_06.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 6")

    img = slide_cta(slides["slide_7_cta"], config)
    p = out_dir / "slide_07.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 7 (CTA)")

    return paths


# ── Pattern 2: The Vibrational Anchor ────────────────────────────────────

_ANCHOR_GRADIENTS = [
    ("#0D0D2B", "#1A0A3D"),
    ("#0A1628", "#0D2B3D"),
    ("#1A0A1A", "#2D1B4E"),
    ("#0A1A10", "#0D2B1A"),
    ("#1A1200", "#2B2000"),
]
_ANCHOR_ACCENTS = ["#F59E0B", "#EC4899", "#10B981", "#60A5FA", "#A78BFA"]


def _gradient_bg(color1_hex: str, color2_hex: str) -> Image.Image:
    c1, c2 = _rgb(color1_hex), _rgb(color2_hex)
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def slide_anchor(n: int, text: str, config: dict) -> Image.Image:
    """Gradient background, bold white text, vibrant accent."""
    grad = _ANCHOR_GRADIENTS[(n - 1) % len(_ANCHOR_GRADIENTS)]
    accent_hex = _ANCHOR_ACCENTS[(n - 1) % len(_ANCHOR_ACCENTS)]

    img = _gradient_bg(grad[0], grad[1])
    draw = ImageDraw.Draw(img)

    _slide_number(draw, n, 7, accent_hex)
    if n < 7:
        _swipe_arrow(draw, accent_hex)

    nc = len(text)
    if nc < 50:
        fs, max_w = 76, W - 120
    elif nc < 100:
        fs, max_w = 60, W - 120
    elif nc < 180:
        fs, max_w = 48, W - 110
    else:
        fs, max_w = 38, W - 100

    font = _font(fs, bold=True)
    lh = int(fs * 1.52)
    lines = _wrap(text, font, draw, max_w)
    total_h = len(lines) * lh
    y0 = (H - total_h) // 2

    _accent_line(img, W // 2, y0 - 40, 64, accent_hex, alpha=200)

    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    _accent_line(img, W // 2, y0 + total_h + 34, 64, accent_hex, alpha=200)

    return img


def slide_anchor_hook(hook_text: str, bg_bytes: bytes, config: dict) -> Image.Image:
    """Pattern 2 Slide 1: AI background with bold hook text."""
    bg = _crop_bg(bg_bytes)

    # Warm gradient overlay instead of pure black
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    start = int(H * 0.25)
    for y in range(start, H):
        t = (y - start) / (H - start)
        a = int(min(1.0, t * 1.6) * 230)
        gd.line([(0, y), (W, y)], fill=(10, 5, 20, a))
    bg = bg.convert("RGBA")
    bg.paste(grad, mask=grad)
    bg = bg.convert("RGB")

    accent_hex = _ANCHOR_ACCENTS[0]
    draw = ImageDraw.Draw(bg)
    _slide_number(draw, 1, 7, accent_hex)
    _swipe_arrow(draw, accent_hex)

    max_w = W - 120
    for fs in (72, 62, 52, 44, 38):
        font = _font(fs, bold=True)
        lines = _wrap(hook_text, font, draw, max_w)
        lh = int(fs * 1.38)
        if len(lines) * lh < H * 0.38:
            break

    lh = int(fs * 1.38)
    y0 = int(H * 0.55)
    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    return bg


def slide_anchor_cta(cta_text: str, config: dict) -> Image.Image:
    """Pattern 2 CTA slide with gradient background."""
    grad = _ANCHOR_GRADIENTS[0]
    accent_hex = _ANCHOR_ACCENTS[1]
    handle = config.get("instagram_handle", "")

    img = _gradient_bg(grad[0], grad[1])
    draw = ImageDraw.Draw(img)
    _slide_number(draw, 7, 7, accent_hex)

    cta_font = _font(52, bold=True)
    handle_font = _font(28, italic=True)
    lh = int(52 * 1.42)

    lines = _wrap(cta_text, cta_font, draw, W - 160)
    cta_h = len(lines) * lh
    divider_gap = 40
    handle_h = 50 if handle else 0
    block = cta_h + divider_gap + handle_h
    y0 = (H - block) // 2

    _accent_line(img, W // 2, y0 - 36, 60, accent_hex, alpha=200)

    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, cta_font)) // 2
        draw.text((x, y), line, font=cta_font, fill=(255, 255, 255))

    _accent_line(img, W // 2, y0 + cta_h + divider_gap // 2, 44, accent_hex, alpha=140)

    if handle:
        hw = _tw(draw, handle, handle_font)
        draw.text(((W - hw) // 2, y0 + cta_h + divider_gap), handle,
                  font=handle_font, fill=_rgba(accent_hex, 210))

    return img


def build_carousel_anchor(slides: dict, bg_bytes: bytes, config: dict, out_dir: Path) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    print("  Building slides (Pattern: Vibrational Anchor)...")

    img = slide_anchor_hook(slides["slide_1_hook"], bg_bytes, config)
    p = out_dir / "slide_01.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 1 (hook)")

    for n in range(2, 7):
        text = slides.get(f"slide_{n}", "")
        img = slide_anchor(n, text, config)
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n}")

    img = slide_anchor_cta(slides["slide_7_cta"], config)
    p = out_dir / "slide_07.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 7 (CTA)")

    return paths


# ── Main dispatcher ───────────────────────────────────────────────────────

def build_carousel(slides: dict, bg_bytes: bytes, config: dict, out_dir: Path) -> list:
    """
    Build carousel — dispatches to the right pattern builder.
    slides must contain a 'pattern' key: 'gap', 'cosmic_duality', or 'vibrational_anchor'
    """
    pattern = slides.get("pattern", "gap")
    if pattern == "cosmic_duality":
        return build_carousel_cosmic(slides, bg_bytes, config, out_dir)
    elif pattern == "vibrational_anchor":
        return build_carousel_anchor(slides, bg_bytes, config, out_dir)
    else:
        return build_carousel_gap(slides, bg_bytes, config, out_dir)
