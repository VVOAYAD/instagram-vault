"""
Image Maker — creates 1080x1080 typographic images for Instagram.
Called automatically by generate.py, or standalone:
  python image_maker.py "Your text here" "Optional second line"
"""

import os
import re
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# ── Fonts ─────────────────────────────────────────────────────────────────

# Windows font paths, in preference order
_SERIF_FONTS = [
    "C:/Windows/Fonts/georgia.ttf",
    "C:/Windows/Fonts/Georgia.ttf",
    "C:/Windows/Fonts/Garamond.ttf",
    "C:/Windows/Fonts/garamond.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/Times New Roman.ttf",
]
_SERIF_ITALIC = [
    "C:/Windows/Fonts/georgiai.ttf",
    "C:/Windows/Fonts/timesi.ttf",
    "C:/Windows/Fonts/Garamondi.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
_SANS_FONTS = [
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/Calibri.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/Segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/Arial.ttf",
]

_font_cache: dict = {}


def _load_font(size: int, style: str = "serif") -> ImageFont.FreeTypeFont:
    key = (size, style)
    if key in _font_cache:
        return _font_cache[key]

    candidates = {
        "serif": _SERIF_FONTS,
        "italic": _SERIF_ITALIC,
        "sans": _SANS_FONTS,
    }.get(style, _SERIF_FONTS)

    for path in candidates:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                _font_cache[key] = font
                return font
            except Exception:
                continue

    # Ultimate fallback
    try:
        font = ImageFont.load_default(size=size)
    except TypeError:
        font = ImageFont.load_default()
    _font_cache[key] = font
    return font


# ── Color helpers ─────────────────────────────────────────────────────────

def _hex_rgb(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i: i + 2], 16) for i in (0, 2, 4))


def _with_alpha(rgb: tuple, alpha: int) -> tuple:
    return (*rgb, alpha)


# ── Drawing helpers ───────────────────────────────────────────────────────

def _text_size(draw: ImageDraw.Draw, text: str, font) -> tuple:
    """Returns (width, height) of text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _wrap_line(line: str, font, max_px: int, draw: ImageDraw.Draw) -> list:
    """Wrap a single string so each part fits within max_px."""
    words = line.split()
    result, current = [], []
    for word in words:
        test = " ".join(current + [word])
        w, _ = _text_size(draw, test, font)
        if w <= max_px:
            current.append(word)
        else:
            if current:
                result.append(" ".join(current))
            current = [word]
    if current:
        result.append(" ".join(current))
    return result or [""]


# ── Main function ─────────────────────────────────────────────────────────

def create_image(
    text_lines: list,
    entry_title: str,
    config: dict,
    output_path: str = None,
) -> str:
    """
    Create a 1080x1080 typographic image.
    text_lines: 1–3 strings for overlay text
    Returns saved image path.
    """
    W, H = 1080, 1080
    style = config.get("image_style", {})
    bg_rgb = _hex_rgb(style.get("background", "#0D0D0D"))
    text_rgb = _hex_rgb(style.get("text_color", "#F0EBE0"))
    accent_rgb = _hex_rgb(style.get("accent_color", "#9B7D52"))
    handle = config.get("instagram_handle", "")

    # ── Canvas ────────────────────────────────────────────────────────────
    img = Image.new("RGB", (W, H), bg_rgb)
    draw = ImageDraw.Draw(img)

    # Subtle corner darkening (no per-pixel loop)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for i in range(12):
        alpha = int(18 - i * 1.5)
        margin = i * 12
        ov_draw.rectangle(
            [margin, margin, W - margin, H - margin],
            outline=(0, 0, 0, alpha),
            width=14,
        )
    img.paste(overlay, mask=overlay)
    draw = ImageDraw.Draw(img)

    # ── Text layout ────────────────────────────────────────────────────────
    lines = [l.strip() for l in text_lines if l.strip()]
    if not lines:
        lines = ["—"]

    PADDING = 100
    MAX_TEXT_W = W - PADDING * 2

    # Choose initial font size based on content
    total_chars = sum(len(l) for l in lines)
    if len(lines) == 1 and total_chars <= 20:
        font_size = 80
    elif len(lines) == 1 and total_chars <= 35:
        font_size = 68
    elif len(lines) <= 2 and total_chars <= 55:
        font_size = 58
    elif total_chars <= 90:
        font_size = 50
    else:
        font_size = 44

    font = _load_font(font_size)

    # Wrap lines that are too wide
    wrapped = []
    for line in lines:
        wrapped.extend(_wrap_line(line, font, MAX_TEXT_W, draw))

    # Recalculate if too many lines after wrapping
    if len(wrapped) > 5:
        font_size = max(32, font_size - 10)
        font = _load_font(font_size)
        wrapped = []
        for line in lines:
            wrapped.extend(_wrap_line(line, font, MAX_TEXT_W, draw))

    line_h = int(font_size * 1.4)
    total_text_h = len(wrapped) * line_h
    y_center = H // 2
    y_start = y_center - total_text_h // 2

    # ── Decorative top line ───────────────────────────────────────────────
    accent_alpha = 160
    accent_rgba = _with_alpha(accent_rgb, accent_alpha)
    line_y_top = y_start - 36
    _draw_accent_line(img, W // 2, line_y_top, 56, accent_rgba)

    # ── Main text ─────────────────────────────────────────────────────────
    for i, line in enumerate(wrapped):
        y = y_start + i * line_h
        tw, _ = _text_size(draw, line, font)
        x = (W - tw) // 2

        # Shadow
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 90))
        # Main
        draw.text((x, y), line, font=font, fill=text_rgb)

    # ── Decorative bottom line ────────────────────────────────────────────
    line_y_bot = y_start + total_text_h + 22
    _draw_accent_line(img, W // 2, line_y_bot, 56, accent_rgba)

    # ── Handle watermark ─────────────────────────────────────────────────
    if handle:
        handle_font = _load_font(26, "italic")
        handle_color = _with_alpha(accent_rgb, 140)
        hw, _ = _text_size(draw, handle, handle_font)
        draw.text(((W - hw) // 2, H - 58), handle, font=handle_font, fill=handle_color)

    # ── Save ──────────────────────────────────────────────────────────────
    if output_path is None:
        OUTPUT_DIR.mkdir(exist_ok=True)
        slug = re.sub(r"[^\w]", "_", entry_title.lower())[:30].strip("_")
        output_path = str(OUTPUT_DIR / f"image_{slug}.png")

    img.save(output_path, "PNG")
    print(f"🖼   Image saved: {output_path}")
    return output_path


def _draw_accent_line(img: Image.Image, cx: int, y: int, half_w: int, color_rgba: tuple):
    """Draw a thin horizontal accent line with alpha."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.line([(cx - half_w, y), (cx + half_w, y)], fill=color_rgba, width=1)
    img.paste(overlay, mask=overlay)


# ── Standalone CLI ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python image_maker.py 'Line 1' 'Line 2' 'Line 3'")
        sys.exit(1)

    config_path = Path(__file__).parent / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}

    lines = sys.argv[1:]
    out = create_image(lines, "preview", config)
    print(f"Done: {out}")
