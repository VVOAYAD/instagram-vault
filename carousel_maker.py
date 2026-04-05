"""
Builds all 7 carousel slides as 1080x1080 JPEG images.

Five patterns:
  gap                — The Gap: dark bg, serif text, gold accents
  cosmic_duality     — The Cosmic Duality: single words on AI bg, neon glow
  vibrational_anchor — The Vibrational Anchor: gradient bg, bold white text
  alien_affirmation  — The Alien Affirmation: full image, one affirmation per slide
  anime_meme         — The Anime Meme: full image, one caption per slide (anime subtitle style)

All slides use the AI-generated background for visual consistency.
"""

import io
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1080

# ── Fonts ─────────────────────────────────────────────────────────────────

_FONTS_DIR = Path(__file__).parent / "fonts"

_SERIF = [
    str(_FONTS_DIR / "PlayfairDisplay-Regular.ttf"),
    "C:/Windows/Fonts/cambria.ttc",
    "C:/Windows/Fonts/georgia.ttf",
    "C:/Windows/Fonts/Georgia.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_ITALIC = [
    str(_FONTS_DIR / "PlayfairDisplay-Regular.ttf"),
    "C:/Windows/Fonts/cambriai.ttf",
    "C:/Windows/Fonts/georgiai.ttf",
    "C:/Windows/Fonts/timesi.ttf",
    "C:/Windows/Fonts/ariali.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_BOLD = [
    str(_FONTS_DIR / "Montserrat-Bold.ttf"),
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
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

def _clean(text: str) -> str:
    """Replace unicode characters Playfair Display doesn't render cleanly."""
    return (text
            .replace("\u2014", " - ")    # em dash — replace with ASCII dash
            .replace("\u2013", " - ")    # en dash
            .replace("\u2018", "'")      # left single quote
            .replace("\u2019", "'")      # right single quote
            .replace("\u201c", '"')      # left double quote
            .replace("\u201d", '"')      # right double quote
            .replace("\u2026", "...")    # ellipsis
            )


def _tw(draw: ImageDraw.Draw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0]


def _th(draw: ImageDraw.Draw, text: str, font) -> int:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[3] - bb[1]


def _wrap(text: str, font, draw: ImageDraw.Draw, max_px: int) -> list:
    words = _clean(text).split()
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


# ── Background helpers ────────────────────────────────────────────────────

def _crop_bg(bg_bytes: bytes, variation: int = 0) -> Image.Image:
    """Load image bytes, crop to square, resize to 1080.
    variation 0-4 gives slightly different crops for visual diversity."""
    bg = Image.open(io.BytesIO(bg_bytes)).convert("RGB")
    bw, bh = bg.size
    s = min(bw, bh)
    offsets = [(0, 0), (-30, -30), (30, -30), (-30, 30), (30, 30)]
    ox, oy = offsets[variation % len(offsets)]
    cx = (bw - s) // 2 + ox
    cy = (bh - s) // 2 + oy
    cx = max(0, min(cx, bw - s))
    cy = max(0, min(cy, bh - s))
    bg = bg.crop((cx, cy, cx + s, cy + s))
    return bg.resize((W, H), Image.LANCZOS)


def _dimmed_ai_bg(bg_bytes: bytes, overlay_alpha: int = 205, blur: float = 1.5,
                  variation: int = 0) -> Image.Image:
    """AI background heavily dimmed for body slides — keeps the cinematic feel
    without fighting the text for attention."""
    bg = _crop_bg(bg_bytes, variation=variation)
    if blur > 0:
        bg = bg.filter(ImageFilter.GaussianBlur(blur))
    veil = Image.new("RGBA", (W, H), (0, 0, 0, overlay_alpha))
    bg = bg.convert("RGBA")
    bg.paste(veil, mask=veil)
    return bg.convert("RGB")


# ── Shared UI elements ────────────────────────────────────────────────────

def _slide_number(draw: ImageDraw.Draw, n: int, total: int, accent: str):
    label = f"{n}  /  {total}"
    font = _font(22, italic=True)
    w = _tw(draw, label, font)
    draw.text((W - 56 - w, 50), label, font=font, fill=_rgba(accent, 130))


def _swipe_arrow(draw: ImageDraw.Draw, accent: str):
    """Geometric chevron pair — no font dependency, always renders."""
    color = _rgba(accent, 150)
    x, y = W - 64, H - 56
    size = 11
    gap = 14
    for dx in (0, gap):
        ax = x + dx
        draw.line([(ax, y - size), (ax + size, y), (ax, y + size)], fill=color, width=2)


def _accent_line(img: Image.Image, cx: int, y: int, half_w: int, accent: str, alpha: int = 150):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.line([(cx - half_w, y), (cx + half_w, y)], fill=_rgba(accent, alpha), width=1)
    img.paste(ov, mask=ov)


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


def slide_content(n: int, text: str, eyebrow: str, config: dict, bg_bytes: bytes = None) -> Image.Image:
    text_color = config.get("image_style", {}).get("text_color", "#F0EBE0")
    accent = config.get("image_style", {}).get("accent_color", "#9B7D52")

    # Use AI background (heavily dimmed) when available — keeps the carousel
    # cinematic rather than cutting to flat black after slide 1
    if bg_bytes:
        variation = n % 5
        img = _dimmed_ai_bg(bg_bytes, overlay_alpha=200, blur=2.0, variation=variation)
    else:
        bg_color = _rgb(config.get("image_style", {}).get("background", "#0D0D0D"))
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
    lines = _wrap(text, font, draw, max_w)
    sample_bb = draw.textbbox((0, 0), "Ag", font=font)
    lh = int((sample_bb[3] - sample_bb[1]) * 1.55)
    text_h = len(lines) * lh

    eb_font = _font(22, italic=True)
    eb_h = 44 if eyebrow.strip() else 0
    gap = 20
    block = eb_h + (gap if eyebrow.strip() else 0) + text_h
    y0 = (H - block) // 2

    _accent_line(img, W // 2, y0 - 30, 52, accent)

    if eyebrow.strip():
        label = _clean(eyebrow).strip().upper()
        ew = _tw(draw, label, eb_font)
        draw.text(((W - ew) // 2, y0), label, font=eb_font, fill=_rgba(accent, 190))

    ty = y0 + eb_h + (gap if eyebrow.strip() else 0)
    for i, line in enumerate(lines):
        y = ty + i * lh
        x = (W - _tw(draw, line, font)) // 2
        # Soft shadow for readability on AI bg
        draw.text((x + 1, y + 1), line, font=font, fill=(0, 0, 0, 120))
        draw.text((x, y), line, font=font, fill=_rgb(text_color))

    _accent_line(img, W // 2, ty + text_h + 24, 52, accent)

    return img


def slide_cta(cta_text: str, config: dict, bg_bytes: bytes = None) -> Image.Image:
    text_color = config.get("image_style", {}).get("text_color", "#F0EBE0")
    accent = config.get("image_style", {}).get("accent_color", "#9B7D52")
    handle = config.get("instagram_handle", "")

    if bg_bytes:
        img = _dimmed_ai_bg(bg_bytes, overlay_alpha=215, blur=3.0, variation=0)
    else:
        bg_color = _rgb(config.get("image_style", {}).get("background", "#0D0D0D"))
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
        draw.text((x + 1, y + 1), line, font=cta_font, fill=(0, 0, 0, 100))
        draw.text((x, y), line, font=cta_font, fill=_rgb(text_color))

    _accent_line(img, W // 2, y0 + cta_h + divider_gap // 2, 40, accent, alpha=110)

    if handle:
        hw = _tw(draw, handle, handle_font)
        draw.text(((W - hw) // 2, y0 + cta_h + divider_gap), handle,
                  font=handle_font, fill=_rgba(accent, 200))

    return img


def build_carousel_gap(slides: dict, bg_list: list, config: dict, out_dir: Path) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    print("  Building slides (Pattern: The Gap)...")

    img = slide_hook(slides["slide_1_hook"], bg_list[0], config)
    p = out_dir / "slide_01.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 1 (hook)")

    for n in range(2, 7):
        data = slides.get(f"slide_{n}", {})
        img = slide_content(n, data.get("text", ""), data.get("eyebrow", ""), config, bg_list[n - 1])
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n}")

    img = slide_cta(slides["slide_7_cta"], config, bg_list[6])
    p = out_dir / "slide_07.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 7 (CTA)")

    return paths


# ── Pattern 1: The Cosmic Duality ─────────────────────────────────────────

_COSMIC_ACCENT = "#C4A97D"  # single warm gold — the image provides all other color
_COSMIC_FONT = str(_FONTS_DIR / "CormorantGaramond-LightItalic.ttf")  # thin elegant serif

# Vertical position of word per slide (fraction of H for the text baseline)
_COSMIC_WORD_Y = [0.12, 0.44, 0.72, 0.14]  # slides 1-4: top / center / lower / top


def _cosmic_font(size: int) -> ImageFont.FreeTypeFont:
    """Cormorant Garamond Light Italic — falls back to Playfair if missing."""
    key = ("cosmic", size)
    if key in _cache:
        return _cache[key]
    for path in [_COSMIC_FONT] + _ITALIC:
        if os.path.exists(path):
            try:
                f = ImageFont.truetype(path, size)
                _cache[key] = f
                return f
            except Exception:
                continue
    f = ImageFont.load_default()
    _cache[key] = f
    return f


def _spaced_width(draw: ImageDraw.Draw, text: str, font, spacing: int) -> int:
    """Total pixel width of text with per-character spacing."""
    total = 0
    for i, ch in enumerate(text):
        bb = draw.textbbox((0, 0), ch, font=font)
        total += bb[2] - bb[0]
        if i < len(text) - 1:
            total += spacing
    return total


def _draw_spaced_glow(img: Image.Image, text: str, x: int, y: int,
                      font, fill_rgb: tuple, spacing: int,
                      glow_color: tuple = (200, 180, 255), glow_radius: int = 18):
    """Draw spaced text with a soft gaussian glow halo behind it."""
    # ── Build the text on a transparent layer ────────────────────────────
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(text_layer)
    cx = x
    for ch in text:
        td.text((cx, y), ch, font=font, fill=(*fill_rgb, 255))
        bb = td.textbbox((0, 0), ch, font=font)
        cx += (bb[2] - bb[0]) + spacing

    # ── Glow: colorize the text layer, blur it, composite under text ─────
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    cx = x
    for ch in text:
        gd.text((cx, y), ch, font=font, fill=(*glow_color, 200))
        bb = gd.textbbox((0, 0), ch, font=font)
        cx += (bb[2] - bb[0]) + spacing
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow_radius))

    # Composite: glow first, then sharp text on top
    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, glow_layer)
    img_rgba = Image.alpha_composite(img_rgba, text_layer)
    return img_rgba.convert("RGB")


def slide_cosmic_word(n: int, word: str, bg_bytes: bytes, config: dict) -> Image.Image:
    """Single spaced word floating over AI background. Image is the hero."""
    # Very light veil — let the image breathe
    bg = _crop_bg(bg_bytes, variation=n)
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 55))
    bg = bg.convert("RGBA")
    bg.paste(veil, mask=veil)
    bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)
    _slide_number(draw, n, 7, _COSMIC_ACCENT)
    _swipe_arrow(draw, _COSMIC_ACCENT)

    word = _clean(word).upper()
    spacing = 18

    # Find largest size that fits within W - 160
    for fs in (100, 86, 72, 60, 50):
        font = _cosmic_font(fs)
        sw = _spaced_width(draw, word, font, spacing)
        if sw <= W - 160:
            break

    sw = _spaced_width(draw, word, font, spacing)

    # Vertical position varies per slide
    y_frac = _COSMIC_WORD_Y[(n - 1) % len(_COSMIC_WORD_Y)]
    y = int(H * y_frac)
    x = (W - sw) // 2

    # Cream text with soft luminous glow
    bg = _draw_spaced_glow(bg, word, x, y, font,
                           fill_rgb=_rgb("#F0EBE0"),
                           spacing=spacing,
                           glow_color=(220, 200, 255),
                           glow_radius=20)
    return bg


def slide_cosmic_reveal(n: int, text: str, bg_bytes: bytes, config: dict) -> Image.Image:
    """Full revelation sentence — the gut-punch. Image stays visible, text is the hero."""
    bg = _dimmed_ai_bg(bg_bytes, overlay_alpha=100, blur=0.8, variation=n)

    accent_hex = "#C4A97D"
    draw = ImageDraw.Draw(bg)
    _slide_number(draw, n, 7, accent_hex)
    if n < 7:
        _swipe_arrow(draw, accent_hex)

    # Position at top third — image fills the rest
    max_w = W - 100
    for fs in (76, 64, 54, 46, 38):
        font = _font(fs, italic=True)
        lines = _wrap(text, font, draw, max_w)
        lh = int(fs * 1.45)
        if len(lines) * lh < H * 0.42:
            break

    lh = int(fs * 1.45)
    total_h = len(lines) * lh
    y0 = int(H * 0.10)

    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        # Draw glow per line
        bg = _draw_spaced_glow(bg, line, x, y, font,
                               fill_rgb=_rgb("#F0EBE0"),
                               spacing=0,
                               glow_color=(220, 200, 255),
                               glow_radius=16)
        draw = ImageDraw.Draw(bg)

    # Single thin accent line below the text
    _accent_line(bg, W // 2, y0 + total_h + 20, 70, accent_hex, alpha=120)

    return bg


def build_carousel_cosmic(slides: dict, bg_list: list, config: dict, out_dir: Path) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    print("  Building slides (Pattern: Cosmic Duality)...")

    for n in range(1, 5):
        word = slides.get(f"slide_{n}_word", "")
        img = slide_cosmic_word(n, word, bg_list[n - 1], config)
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n} ({word})")

    img = slide_cosmic_reveal(5, slides.get("slide_5_revelation", ""), bg_list[4], config)
    p = out_dir / "slide_05.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 5 (revelation)")

    data = slides.get("slide_6", {})
    img = slide_content(6, data.get("text", ""), data.get("eyebrow", ""), config, bg_list[5])
    p = out_dir / "slide_06.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 6")

    img = slide_cta(slides["slide_7_cta"], config, bg_list[6])
    p = out_dir / "slide_07.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 7 (CTA)")

    return paths


# ── Pattern 2: The Vibrational Anchor ────────────────────────────────────

_ANCHOR_ACCENTS = ["#F59E0B", "#EC4899", "#10B981", "#60A5FA", "#A78BFA"]


def slide_anchor(n: int, text: str, config: dict, bg_bytes: bytes = None) -> Image.Image:
    """Bold white text on AI background (or deep gradient fallback)."""
    accent_hex = _ANCHOR_ACCENTS[(n - 1) % len(_ANCHOR_ACCENTS)]

    if bg_bytes:
        variation = (n + 2) % 5
        img = _dimmed_ai_bg(bg_bytes, overlay_alpha=195, blur=2.5, variation=variation)
    else:
        # Fallback gradient if no AI bg
        _ANCHOR_GRADIENTS = [
            ("#0D0D2B", "#1A0A3D"), ("#0A1628", "#0D2B3D"),
            ("#1A0A1A", "#2D1B4E"), ("#0A1A10", "#0D2B1A"), ("#1A1200", "#2B2000"),
        ]
        grad = _ANCHOR_GRADIENTS[(n - 1) % len(_ANCHOR_GRADIENTS)]
        c1, c2 = _rgb(grad[0]), _rgb(grad[1])
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        for row in range(H):
            t = row / H
            r = int(c1[0] * (1 - t) + c2[0] * t)
            g = int(c1[1] * (1 - t) + c2[1] * t)
            b = int(c1[2] * (1 - t) + c2[2] * t)
            d.line([(0, row), (W, row)], fill=(r, g, b))

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
    lines = _wrap(text, font, draw, max_w)
    sample_bb = draw.textbbox((0, 0), "Ag", font=font)
    lh = int((sample_bb[3] - sample_bb[1]) * 1.5)
    total_h = len(lines) * lh
    y0 = (H - total_h) // 2

    _accent_line(img, W // 2, y0 - 44, 64, accent_hex, alpha=200)

    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        # Shadow for readability on AI bg
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 140))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    _accent_line(img, W // 2, y0 + total_h + 34, 64, accent_hex, alpha=200)

    return img


def slide_anchor_hook(hook_text: str, bg_bytes: bytes, config: dict) -> Image.Image:
    """Pattern 2 Slide 1: AI background with bold hook text."""
    bg = _crop_bg(bg_bytes)

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


def slide_anchor_cta(cta_text: str, config: dict, bg_bytes: bytes = None) -> Image.Image:
    """Pattern 2 CTA slide."""
    accent_hex = _ANCHOR_ACCENTS[1]
    handle = config.get("instagram_handle", "")

    if bg_bytes:
        img = _dimmed_ai_bg(bg_bytes, overlay_alpha=210, blur=3.0, variation=1)
    else:
        c1, c2 = _rgb("#0D0D2B"), _rgb("#1A0A3D")
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        for row in range(H):
            t = row / H
            r = int(c1[0] * (1 - t) + c2[0] * t)
            g = int(c1[1] * (1 - t) + c2[1] * t)
            b = int(c1[2] * (1 - t) + c2[2] * t)
            d.line([(0, row), (W, row)], fill=(r, g, b))

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
        draw.text((x + 2, y + 2), line, font=cta_font, fill=(0, 0, 0, 120))
        draw.text((x, y), line, font=cta_font, fill=(255, 255, 255))

    _accent_line(img, W // 2, y0 + cta_h + divider_gap // 2, 44, accent_hex, alpha=140)

    if handle:
        hw = _tw(draw, handle, handle_font)
        draw.text(((W - hw) // 2, y0 + cta_h + divider_gap), handle,
                  font=handle_font, fill=_rgba(accent_hex, 210))

    return img


def build_carousel_anchor(slides: dict, bg_list: list, config: dict, out_dir: Path) -> list:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    print("  Building slides (Pattern: Vibrational Anchor)...")

    img = slide_anchor_hook(slides["slide_1_hook"], bg_list[0], config)
    p = out_dir / "slide_01.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 1 (hook)")

    for n in range(2, 7):
        text = slides.get(f"slide_{n}", "")
        img = slide_anchor(n, text, config, bg_list[n - 1])
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n}")

    img = slide_anchor_cta(slides["slide_7_cta"], config, bg_list[6])
    p = out_dir / "slide_07.jpg"
    img.save(str(p), "JPEG", quality=92)
    paths.append(p)
    print("    ✓ Slide 7 (CTA)")

    return paths


# ── Pattern 3: The Alien Affirmation ─────────────────────────────────────

def _tracked_caps(text: str, spacing: int = 2) -> str:
    """ALL CAPS with wide letter tracking — spaces inserted between each character."""
    return (" " * spacing).join(_clean(text).upper())


def slide_affirmation(n: int, text: str, bg_bytes: bytes, config: dict, total: int = 7) -> Image.Image:
    """Full-bleed image, light veil, ALL CAPS tracked text in lower third.
    Matches the reference aesthetic: illustrated alien, deep navy, glitter stars, spaced caps."""
    bg = _crop_bg(bg_bytes, variation=n % 5)

    # Very light veil — image is the hero
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 50))
    bg = bg.convert("RGBA")
    bg.paste(veil, mask=veil)

    # Gradient at bottom so text is always readable
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    start = int(H * 0.60)
    for y in range(start, H):
        t = (y - start) / (H - start)
        a = int(min(1.0, t * 1.9) * 195)
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    bg.paste(grad, mask=grad)
    bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)
    accent = "#FFFFFF"
    _slide_number(draw, n, total, accent)
    if n < total:
        _swipe_arrow(draw, accent)

    # Tracking doubles the visual width, so wrap at ~40% of canvas width
    # then shrink font until every tracked line fits within canvas margins
    raw = _clean(text).upper()
    nc = len(raw)
    if nc < 20:
        fs = 36
    elif nc < 40:
        fs = 28
    else:
        fs = 22

    margin = W - 100
    font = _font(fs, bold=False)
    # Wrap using untracked width — allow generous line breaks
    word_lines = _wrap(raw, font, draw, W - 220)
    tracked_lines = [_tracked_caps(line, spacing=2) for line in word_lines]

    # Auto-shrink if any tracked line is wider than canvas
    while any(_tw(draw, tl, font) > margin for tl in tracked_lines) and fs > 14:
        fs -= 2
        font = _font(fs, bold=False)
        word_lines = _wrap(raw, font, draw, W - 220)
        tracked_lines = [_tracked_caps(line, spacing=2) for line in word_lines]

    lh = int(fs * 1.75)
    total_h = len(tracked_lines) * lh
    y0 = int(H * 0.75) - total_h // 2

    for i, line in enumerate(tracked_lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        draw.text((x + 1, y + 1), line, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    return bg


def build_carousel_alien(slides: dict, bg_list: list, config: dict, out_dir: Path) -> list:
    """Alien Affirmation: each of 7 slides = full image + one affirmation."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    print("  Building slides (Pattern: Alien Affirmation)...")

    slide_texts = slides.get("slides", [])
    for n in range(1, 8):
        text = slide_texts[n - 1] if n - 1 < len(slide_texts) else ""
        img = slide_affirmation(n, text, bg_list[n - 1], config, total=7)
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n}: {text[:40]}")

    return paths


# ── Pattern 4: The Anime Meme ─────────────────────────────────────────────

def slide_anime_caption(n: int, text: str, bg_bytes: bytes, config: dict, total: int = 7) -> Image.Image:
    """Full-bleed anime image, black-outlined white caption — anime subtitle style."""
    bg = _crop_bg(bg_bytes, variation=n % 5)

    # Medium veil so text pops without killing the image
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 85))
    bg = bg.convert("RGBA")
    bg.paste(veil, mask=veil)
    bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)
    accent = "#F59E0B"
    _slide_number(draw, n, total, accent)
    if n < total:
        _swipe_arrow(draw, accent)

    text = _clean(text)
    nc = len(text)
    if nc < 30:
        fs, max_w = 72, W - 120
    elif nc < 60:
        fs, max_w = 58, W - 120
    elif nc < 110:
        fs, max_w = 46, W - 110
    else:
        fs, max_w = 36, W - 100

    font = _font(fs, bold=True)
    lines = _wrap(text, font, draw, max_w)
    lh = int(fs * 1.48)
    total_h = len(lines) * lh

    # Vertically centered, nudged slightly below midpoint
    y0 = int(H * 0.54) - total_h // 2

    for i, line in enumerate(lines):
        y = y0 + i * lh
        x = (W - _tw(draw, line, font)) // 2
        # Black outline (anime subtitle look)
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    return bg


def build_carousel_anime(slides: dict, bg_list: list, config: dict, out_dir: Path) -> list:
    """Anime Meme: each of 7 slides = retro anime image + one caption."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    print("  Building slides (Pattern: Anime Meme)...")

    slide_texts = slides.get("slides", [])
    for n in range(1, 8):
        text = slide_texts[n - 1] if n - 1 < len(slide_texts) else ""
        img = slide_anime_caption(n, text, bg_list[n - 1], config, total=7)
        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n}: {text[:40]}")

    return paths


# ── Pattern 5+: Generic builder (for learned patterns) ───────────────────

def build_carousel_generic(slides: dict, bg_list: list, config: dict, out_dir: Path) -> list:
    """
    Generic builder for patterns loaded from learned_patterns.json.
    Visual behaviour is driven by slides['_style'] parameters.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    style = slides.get("_style", {})
    pattern = slides.get("pattern", "generic")
    print(f"  Building slides (Pattern: {slides.get('_display_name', pattern)})...")

    bg_treatment = style.get("bg_treatment", "dim")   # none | dim | very_dim | white_card
    text_position = style.get("text_position", "center")  # center | lower_third | upper
    font_name = style.get("font", "serif")             # serif | bold | italic
    text_color_key = style.get("text_color", "white")  # white | dark
    use_outline = style.get("text_outline", False)
    accent_hex = style.get("accent_color", "#C4A97D")
    show_slide_num = style.get("slide_number", True)
    fixed_header = slides.get("header", "")
    fixed_subtitle = slides.get("subtitle", "")
    slide_texts = slides.get("slides", [])

    text_rgb = (255, 255, 255) if text_color_key == "white" else (20, 20, 30)
    shadow_rgb = (0, 0, 0) if text_color_key == "white" else (200, 200, 210)

    for n in range(1, 8):
        bg_bytes = bg_list[n - 1]
        bg = _crop_bg(bg_bytes, variation=n % 5)

        # ── Background treatment ──────────────────────────────────────────
        if bg_treatment == "none":
            img = bg.convert("RGB")
        elif bg_treatment == "dim":
            veil = Image.new("RGBA", (W, H), (0, 0, 0, 160))
            bg = bg.convert("RGBA")
            bg.paste(veil, mask=veil)
            img = bg.convert("RGB")
        elif bg_treatment == "very_dim":
            veil = Image.new("RGBA", (W, H), (0, 0, 0, 210))
            bg = bg.convert("RGBA")
            bg.paste(veil, mask=veil)
            img = bg.convert("RGB")
        elif bg_treatment == "white_card":
            img = bg.convert("RGB")
            # Draw semi-transparent white card over center
            card_ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            cd = ImageDraw.Draw(card_ov)
            pad_x, pad_y = 90, 100
            cd.rounded_rectangle(
                [pad_x, pad_y, W - pad_x, H - pad_y],
                radius=18, fill=(255, 255, 255, 240)
            )
            img = img.convert("RGBA")
            img.paste(card_ov, mask=card_ov)
            img = img.convert("RGB")
        else:
            img = bg.convert("RGB")

        draw = ImageDraw.Draw(img)

        if show_slide_num:
            _slide_number(draw, n, 7, accent_hex)
            if n < 7:
                _swipe_arrow(draw, accent_hex)

        # ── Fixed header (same on every slide) ───────────────────────────
        header_bottom_y = 0
        card_top = 110 if bg_treatment == "white_card" else 0
        card_bottom = H - 110 if bg_treatment == "white_card" else H

        if fixed_header.strip():
            # Big, prominent header
            h_font = _font(64, italic=(font_name == "italic"))
            h_text = _clean(fixed_header)
            # Auto-shrink header to fit card width
            h_max = W - 240
            while _tw(draw, h_text, h_font) > h_max and h_font.size > 32:
                h_font = _font(h_font.size - 4, italic=(font_name == "italic"))
            hw = _tw(draw, h_text, h_font)
            hx = (W - hw) // 2
            hy = card_top + 60
            draw.text((hx, hy), h_text, font=h_font, fill=text_rgb)
            header_bottom_y = hy + _th(draw, h_text, h_font) + 8

            if fixed_subtitle.strip():
                s_font = _font(32, italic=True)
                s_text = _clean(fixed_subtitle)
                sw = _tw(draw, s_text, s_font)
                draw.text(((W - sw) // 2, header_bottom_y), s_text,
                          font=s_font, fill=_rgba(accent_hex, 210))
                header_bottom_y += _th(draw, s_text, s_font) + 20

            # Divider under header block
            _accent_line(img, W // 2, header_bottom_y + 6, 100, accent_hex, alpha=160)
            header_bottom_y += 28

        # ── Slide text ────────────────────────────────────────────────────
        slide_text = _clean(slide_texts[n - 1] if n - 1 < len(slide_texts) else "")
        nc = len(slide_text)
        if nc < 40:
            fs, max_w = 46, W - 220
        elif nc < 80:
            fs, max_w = 38, W - 200
        elif nc < 140:
            fs, max_w = 32, W - 180
        else:
            fs, max_w = 26, W - 160

        is_bold = font_name == "bold"
        is_italic = font_name == "italic"
        font = _font(fs, italic=is_italic, bold=is_bold)
        lines = _wrap(slide_text, font, draw, max_w)
        lh = int(fs * 1.5)
        total_h = len(lines) * lh

        # Determine vertical position
        usable_top = header_bottom_y if header_bottom_y else card_top + 60
        usable_bottom = card_bottom - 60

        if text_position == "lower_third":
            y0 = usable_bottom - total_h - 60
        elif text_position == "upper":
            y0 = usable_top + 30
        else:  # center
            mid = (usable_top + usable_bottom) // 2
            y0 = mid - total_h // 2

        for i, line in enumerate(lines):
            y = y0 + i * lh
            x = (W - _tw(draw, line, font)) // 2
            if use_outline:
                for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
                    draw.text((x + dx, y + dy), line, font=font, fill=shadow_rgb)
            else:
                draw.text((x + 1, y + 1), line, font=font, fill=(*shadow_rgb, 140))
            draw.text((x, y), line, font=font, fill=text_rgb)

        p = out_dir / f"slide_{n:02d}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(p)
        print(f"    ✓ Slide {n}: {slide_text[:40]}")

    return paths


# ── Main dispatcher ───────────────────────────────────────────────────────

def build_carousel(slides: dict, bg_bytes_input, config: dict, out_dir: Path) -> list:
    """
    Build carousel — dispatches to the right pattern builder.
    bg_bytes_input: either a list of 7 bytes objects (one per slide) or a single bytes object.
    slides must contain a 'pattern' key: 'gap', 'cosmic_duality', or 'vibrational_anchor'
    """
    # Normalise: always work with a list of 7
    if isinstance(bg_bytes_input, (bytes, bytearray)):
        bg_list = [bg_bytes_input] * 7
    else:
        bg_list = list(bg_bytes_input)
        while len(bg_list) < 7:
            bg_list.append(bg_list[-1])

    pattern = slides.get("pattern", "gap")
    if pattern == "cosmic_duality":
        return build_carousel_cosmic(slides, bg_list, config, out_dir)
    elif pattern == "vibrational_anchor":
        return build_carousel_anchor(slides, bg_list, config, out_dir)
    elif pattern == "alien_affirmation":
        return build_carousel_alien(slides, bg_list, config, out_dir)
    elif pattern == "anime_meme":
        return build_carousel_anime(slides, bg_list, config, out_dir)
    elif pattern in ("gap", ""):
        return build_carousel_gap(slides, bg_list, config, out_dir)
    else:
        # Learned patterns — use generic builder
        return build_carousel_generic(slides, bg_list, config, out_dir)
