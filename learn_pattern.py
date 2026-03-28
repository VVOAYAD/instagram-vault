#!/usr/bin/env python3
"""
Learn new carousel patterns from reference images.

Usage:
  python learn_pattern.py

Drop screenshots of Instagram posts you like into pattern_references/.
Run this script. It uses Claude Vision to analyze the images, extracts
the pattern structure and visual style, and adds it to learned_patterns.json.

New patterns immediately join the daily rotation — no code changes needed.
"""

import base64
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
REFS_DIR = BASE_DIR / "pattern_references"
LEARNED_PATH = BASE_DIR / "learned_patterns.json"
PROCESSED_PATH = BASE_DIR / "pattern_references" / "_processed.json"

ANALYSIS_PROMPT = """You are analyzing Instagram carousel post screenshots to extract reusable content patterns.

Study all the images provided. They may show slides from one or more different carousel posts.

For each distinct visual pattern you identify, output a JSON object. Return an ARRAY of pattern objects — one per distinct pattern you find.

Each pattern object must have this exact structure:
{
  "pattern_name": "slug_like_this",
  "display_name": "Human Readable Name",
  "description": "One sentence: what makes this pattern unique and when to use it",
  "slides_count": 7,
  "style": {
    "bg_treatment": "white_card OR dim OR very_dim OR none",
    "text_position": "center OR lower_third OR upper",
    "font": "serif OR bold OR italic",
    "text_color": "white OR dark",
    "text_outline": false,
    "accent_color": "#hexcolor",
    "slide_number": true
  },
  "has_fixed_header": true or false,
  "header_description": "What the fixed header element is (e.g. 'A Quranic phrase in transliteration', or empty string if none)",
  "has_fixed_subtitle": true or false,
  "subtitle_description": "What the subtitle element is (e.g. 'English translation in italics', or empty string if none)",
  "slide_content_style": "One sentence: what each slide's main text should be (e.g. 'One short affirmation', 'A relatable meme caption', 'A reflection on the header concept')",
  "image_prompt": "Detailed Flux 1.1 Pro prompt to generate the background image for this pattern. Be specific about colors, style, composition. End with: NO text NO words NO letters in image",
  "content_tone": "The tone/voice for this pattern (e.g. grounded and confident, playful and relatable, spiritual and sacred)"
}

bg_treatment options:
- white_card: draws a white/light translucent card over the center of the image (for quote-card styles, scripture cards, etc.)
- dim: medium dark overlay (general purpose)
- very_dim: heavy dark overlay (for when text needs maximum contrast)
- none: image shown almost raw (good for when the image IS the content)

Be specific and accurate. The pattern definitions will be used to automatically generate Instagram carousels.

Return ONLY a valid JSON array. No explanation, no markdown, just the array."""


def load_processed() -> set:
    if PROCESSED_PATH.exists():
        return set(json.loads(PROCESSED_PATH.read_text(encoding="utf-8")))
    return set()


def save_processed(processed: set):
    PROCESSED_PATH.write_text(json.dumps(sorted(processed), indent=2), encoding="utf-8")


def load_learned() -> dict:
    if LEARNED_PATH.exists():
        return json.loads(LEARNED_PATH.read_text(encoding="utf-8"))
    return {}


def save_learned(learned: dict):
    LEARNED_PATH.write_text(json.dumps(learned, indent=2, ensure_ascii=False), encoding="utf-8")


def image_to_base64(path: Path) -> tuple:
    """Returns (base64_data, media_type)."""
    ext = path.suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return data, media_type


def build_content_prompt(pattern: dict) -> str:
    """Generate a Claude content prompt for a learned pattern."""
    has_header = pattern.get("has_fixed_header", False)
    has_subtitle = pattern.get("has_fixed_subtitle", False)
    header_desc = pattern.get("header_description", "")
    subtitle_desc = pattern.get("subtitle_description", "")
    slide_style = pattern.get("slide_content_style", "One thought per slide")
    tone = pattern.get("content_tone", "")
    display_name = pattern.get("display_name", pattern["pattern_name"])
    description = pattern.get("description", "")

    header_block = ""
    if has_header:
        header_block = f'  "header": "{header_desc} — keep it concise",\n'
    if has_subtitle:
        header_block += f'  "subtitle": "{subtitle_desc}",\n'

    return f"""Transform this raw download into a 7-slide Instagram carousel using THE {display_name.upper()} pattern.

THE {display_name.upper()}: {description}
Tone: {tone}
Each slide: {slide_style}

TITLE: {{title}}
CONTENT:
{{content}}

Return ONLY valid JSON:
{{{{
  "pattern": "{pattern["pattern_name"]}",
{header_block}  "slides": [
    "Slide 1 — {slide_style}",
    "Slide 2",
    "Slide 3",
    "Slide 4",
    "Slide 5",
    "Slide 6",
    "Slide 7 — the one that lands hardest"
  ],
  "caption": "Full caption — no hashtags. Match the tone: {tone}.",
  "hashtags": ["10", "to", "15", "hashtags"],
  "image_prompt": "{pattern["image_prompt"]}"
}}}}"""


def build_auto_prompt(pattern: dict) -> str:
    """Generate a Claude auto-generate prompt for a learned pattern."""
    display_name = pattern.get("display_name", pattern["pattern_name"])
    description = pattern.get("description", "")
    slide_style = pattern.get("slide_content_style", "One thought per slide")
    has_header = pattern.get("has_fixed_header", False)
    has_subtitle = pattern.get("has_fixed_subtitle", False)

    header_block = ""
    if has_header:
        header_block = '  "_header": "Generated header value",\n'
    if has_subtitle:
        header_block += '  "_subtitle": "Generated subtitle value",\n'

    return f"""Study these existing downloads:

{{context}}

Generate ONE original insight using THE {display_name.upper()} pattern.
{description}

Return ONLY valid JSON:
{{{{
  "pattern": "{pattern["pattern_name"]}",
  "_title": "Name of this insight",
  "_raw_content": "The full download — 3-6 sentences",
{header_block}  "slides": ["Slide 1", "Slide 2", "Slide 3", "Slide 4", "Slide 5", "Slide 6", "Slide 7"],
  "caption": "Full caption — no hashtags",
  "hashtags": ["10", "hashtags"],
  "image_prompt": "{pattern["image_prompt"]}"
}}}}"""


def analyze_images(image_paths: list, api_key: str) -> list:
    """Send images to Claude Vision and get back pattern definitions."""
    import anthropic

    print(f"  Sending {len(image_paths)} images to Claude Vision...")

    content = []
    for path in image_paths:
        data, media_type = image_to_base64(path)
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data}
        })
        content.append({"type": "text", "text": f"[Image: {path.name}]"})

    content.append({"type": "text", "text": ANALYSIS_PROMPT})

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": content}]
    )

    text = next((b.text for b in response.content if b.type == "text"), "")
    # Strip markdown code fences if present
    import re
    text = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("```").strip()

    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\[[\s\S]*\]", text)
        if m:
            return json.loads(m.group())
        raise ValueError(f"Could not parse Claude response as JSON:\n{text[:500]}")


def main():
    REFS_DIR.mkdir(exist_ok=True)

    # Find unprocessed images
    processed = load_processed()
    image_exts = {".jpg", ".jpeg", ".png", ".webp"}
    all_images = sorted(
        p for p in REFS_DIR.iterdir()
        if p.suffix.lower() in image_exts and p.name not in processed
    )

    if not all_images:
        print("No new images in pattern_references/ — nothing to learn.")
        print("Drop screenshots into that folder then run this again.")
        return

    print(f"Found {len(all_images)} new image(s):")
    for p in all_images:
        print(f"  {p.name}")

    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY") or ""
    if not api_key:
        config_path = BASE_DIR / "config.json"
        if config_path.exists():
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            api_key = cfg.get("anthropic_api_key", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    # Analyze
    patterns = analyze_images(all_images, api_key)
    if not patterns:
        print("Claude didn't find any patterns.")
        return

    print(f"\nClaude identified {len(patterns)} pattern(s):")

    learned = load_learned()
    new_count = 0

    for p in patterns:
        slug = p.get("pattern_name", "").strip().lower().replace(" ", "_")
        if not slug:
            continue

        display = p.get("display_name", slug)

        if slug in learned:
            print(f"  ⟳  '{display}' already exists — skipping")
            continue

        # Build prompt templates
        p["content_prompt"] = build_content_prompt(p)
        p["auto_prompt"] = build_auto_prompt(p)
        p["source_images"] = [f"pattern_references/{img.name}" for img in all_images]

        learned[slug] = p
        new_count += 1
        print(f"  ✓  '{display}' added to learned_patterns.json")
        print(f"     Visual: {p.get('style', {}).get('bg_treatment')} bg, "
              f"{p.get('style', {}).get('text_position')} text, "
              f"{p.get('style', {}).get('font')} font")
        print(f"     Each slide: {p.get('slide_content_style', '')}")

    if new_count:
        save_learned(learned)
        save_processed(processed | {p.name for p in all_images})
        print(f"\n✅  {new_count} new pattern(s) saved to learned_patterns.json")
        print("   They will appear in the daily rotation starting tomorrow.")
    else:
        print("\nNo new patterns were added.")


if __name__ == "__main__":
    main()
