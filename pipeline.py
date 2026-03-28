#!/usr/bin/env python3
"""
Cloud pipeline — runs daily via GitHub Actions.
Reads new notes from Downloads/, generates a 7-slide carousel, posts to Instagram.

Two-phase design (GitHub Actions needs to commit images before Instagram can use them):
  python pipeline.py --phase1 --generate-if-empty   # generate content + slides
  git add . && git commit && git push                # (done by the workflow)
  python pipeline.py --phase2                        # post carousel to Instagram

Local dry run (generates everything, skips posting):
  python pipeline.py --phase1 --dry-run
"""

import os
import re
import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

import anthropic

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"

def _get_downloads_dir(config: dict) -> Path:
    """Downloads can live in the Obsidian vault (configured in config.json)
    or fall back to the instagram_system/Downloads folder."""
    custom = config.get("downloads_dir", "")
    if custom:
        p = Path(custom).expanduser()
        if p.exists():
            return p
    return BASE_DIR / "Downloads"
OUTPUT_DIR = BASE_DIR / "output"
PROCESSED_PATH = BASE_DIR / ".processed.json"
PENDING_PATH = BASE_DIR / ".pending_plan.json"


# ── Helpers ────────────────────────────────────────────────────────────────

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_processed():
    if PROCESSED_PATH.exists():
        with open(PROCESSED_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_processed(data):
    with open(PROCESSED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ── Notes reader ───────────────────────────────────────────────────────────

def get_notes(config: dict):
    """Read all .md files from Downloads/ folder."""
    downloads_dir = _get_downloads_dir(config)
    downloads_dir.mkdir(exist_ok=True)
    notes = []
    for path in sorted(downloads_dir.glob("*.md")):
        if path.name.startswith(".") or "example" in path.name.lower():
            continue
        title = path.stem
        raw = path.read_text(encoding="utf-8").strip()
        content = re.sub(rf"^#\s+{re.escape(title)}\s*\n+", "", raw).strip()
        if content:
            notes.append({"id": path.stem, "title": title, "content": content, "path": str(path)})
    return notes


# ── Claude prompts ─────────────────────────────────────────────────────────

SYSTEM = """You are the content engine for a thought leader in consciousness, nervous system reprogramming, and human transformation.

VOICE: {voice}

AESTHETIC: {visual_style}

PHILOSOPHY: {philosophy}

Rule: Never explain. Transmit. Each carousel carries the full feeling on its own."""

# ── Pattern prompts ────────────────────────────────────────────────────────

GAP_ENTRY_PROMPT = """Transform this raw download into a 7-slide Instagram carousel using THE GAP pattern.

THE GAP: You open a gap between what the mind knows and what the body hasn't caught up to yet. Slow, expansive, each slide one thought deeper.

TITLE: {title}
CONTENT:
{content}

Return ONLY valid JSON:
{{
  "pattern": "gap",
  "slide_1_hook": "The hook — opens the gap. Max 10 words.",
  "slide_2": {{"eyebrow": "optional label", "text": "First layer — 1-3 sentences"}},
  "slide_3": {{"eyebrow": "", "text": "Deepen it"}},
  "slide_4": {{"eyebrow": "", "text": "The tension — where the gap lives"}},
  "slide_5": {{"eyebrow": "", "text": "The turn"}},
  "slide_6": {{"eyebrow": "The Shift", "text": "What closes the gap — the felt realization"}},
  "slide_7_cta": "Save this if it hit.",
  "caption": "Full caption — no hashtags. Hook + 3-4 lines + one reflection question.",
  "hashtags": ["10", "to", "15", "hashtags"],
  "image_prompt": "Flux prompt — dark ethereal abstract void, slow luminous light dispersing through black space, ink dissolving in deep water, microscopic cellular forms barely lit, cinematic chiaroscuro, ultra-minimal, photorealistic, NO text, NO words, NO letters in image"
}}"""

COSMIC_ENTRY_PROMPT = """Transform this raw download into a 7-slide Instagram carousel using THE COSMIC DUALITY pattern.

THE COSMIC DUALITY: Single words build a sentence across slides 1-4. Slide 5 is the full revelation. Mystical, authoritative, suspended breath.

TITLE: {title}
CONTENT:
{content}

Return ONLY valid JSON:
{{
  "pattern": "cosmic_duality",
  "slide_1_word": "First word — evocative, mystical (e.g. Remember / Feel / You / Before)",
  "slide_2_word": "Second word — continues the build",
  "slide_3_word": "Third word — tightens",
  "slide_4_word": "Fourth word or short phrase ending with a period",
  "slide_5_revelation": "The complete sentence that slides 1-4 were building toward — short, final, devastating",
  "slide_6": {{"eyebrow": "", "text": "Optional 1-2 sentences of depth, or leave short"}},
  "slide_7_cta": "Save this.",
  "caption": "Full caption — no hashtags. Starts with the revelation, expands.",
  "hashtags": ["10", "to", "15", "hashtags"],
  "image_prompt": "Flux prompt — hyper-detailed 3D neo-classical marble statue, body cracked and split vertically down the center, blinding white-gold light pouring through the split, deep jet-black background, subtle chromatic aberration at crack edges, scattered white and pale pink flowers at the base, teal and violet spectral light halo, cinematic studio lighting, photorealistic render, ultra-sharp, NO text, NO words, NO letters in image"
}}"""

ANCHOR_ENTRY_PROMPT = """Transform this raw download into a 7-slide Instagram carousel using THE VIBRATIONAL ANCHOR pattern.

THE VIBRATIONAL ANCHOR: Direct, grounding, rhythmic. Short punchy sentences. "I" and "you" statements. Each slide is a breath, a reset, a permission slip.

TITLE: {title}
CONTENT:
{content}

Return ONLY valid JSON:
{{
  "pattern": "vibrational_anchor",
  "slide_1_hook": "Hook — a goal, intention, or state of being. One sentence.",
  "slide_2": "A grounding statement or reframe — 1-2 sentences",
  "slide_3": "A permission slip — what they're allowed to feel or do",
  "slide_4": "The shift — what changes when they accept this",
  "slide_5": "An anchor — a simple truth to return to",
  "slide_6": "Final affirmation — the state to embody. Short and complete.",
  "slide_7_cta": "Save this if it hit.",
  "caption": "Full caption — no hashtags. Warm, direct, encouraging.",
  "hashtags": ["10", "to", "15", "hashtags"],
  "image_prompt": "Flux prompt — retro-surrealist dreamcore, lone glowing human silhouette standing in vast surreal landscape, warm amber-peach-violet gradient sky, soft film grain texture, muted neon glow, painterly atmosphere, golden hour light bleeding through clouds, slight lens distortion, cinematic widescreen feel, NO text, NO words, NO letters in image"
}}"""

# Auto-generate versions (no note context)
GAP_AUTO_PROMPT = """Study these existing downloads:

{context}

Generate ONE original new insight using THE GAP pattern. Same frequency, fresh expression.

Return ONLY valid JSON:
{{
  "pattern": "gap",
  "_title": "Name of this insight",
  "_raw_content": "The full download — 3-6 sentences",
  "slide_1_hook": "Hook — max 10 words",
  "slide_2": {{"eyebrow": "", "text": "First layer"}},
  "slide_3": {{"eyebrow": "", "text": "Deepen"}},
  "slide_4": {{"eyebrow": "", "text": "Tension"}},
  "slide_5": {{"eyebrow": "", "text": "Turn"}},
  "slide_6": {{"eyebrow": "The Shift", "text": "Felt realization"}},
  "slide_7_cta": "Save this if it hit.",
  "caption": "Full caption — no hashtags",
  "hashtags": ["10", "hashtags"],
  "image_prompt": "Dark ethereal abstract void, luminous light dissolving through black space, NO text, NO words in image"
}}"""

COSMIC_AUTO_PROMPT = """Study these existing downloads:

{context}

Generate ONE original new insight using THE COSMIC DUALITY pattern. Single words building to revelation.

Return ONLY valid JSON:
{{
  "pattern": "cosmic_duality",
  "_title": "Name of this insight",
  "_raw_content": "The full download — 3-6 sentences",
  "slide_1_word": "First word",
  "slide_2_word": "Second word",
  "slide_3_word": "Third word",
  "slide_4_word": "Fourth word.",
  "slide_5_revelation": "The full revelation sentence",
  "slide_6": {{"eyebrow": "", "text": "Brief depth"}},
  "slide_7_cta": "Save this.",
  "caption": "Full caption — no hashtags",
  "hashtags": ["10", "hashtags"],
  "image_prompt": "Hyper-detailed 3D neo-classical marble statue split down the center, light pouring through, flowers at base, deep black background, NO text, NO words in image"
}}"""

ANCHOR_AUTO_PROMPT = """Study these existing downloads:

{context}

Generate ONE original new insight using THE VIBRATIONAL ANCHOR pattern. Grounding, rhythmic, direct.

Return ONLY valid JSON:
{{
  "pattern": "vibrational_anchor",
  "_title": "Name of this insight",
  "_raw_content": "The full download — 3-6 sentences",
  "slide_1_hook": "Hook — one sentence",
  "slide_2": "Grounding statement",
  "slide_3": "Permission slip",
  "slide_4": "The shift",
  "slide_5": "Anchor",
  "slide_6": "Final affirmation",
  "slide_7_cta": "Save this if it hit.",
  "caption": "Full caption — no hashtags",
  "hashtags": ["10", "hashtags"],
  "image_prompt": "Retro-surrealist dreamcore, glowing human silhouette, warm amber-violet sky, film grain, NO text, NO words in image"
}}"""

EMPTY_VAULT_PROMPTS = {
    "gap": GAP_AUTO_PROMPT.replace("{context}", "Write from pure consciousness wisdom — no context needed."),
    "cosmic_duality": COSMIC_AUTO_PROMPT.replace("{context}", "Write from pure consciousness wisdom — no context needed."),
    "vibrational_anchor": ANCHOR_AUTO_PROMPT.replace("{context}", "Write from pure consciousness wisdom — no context needed."),
}

_PATTERN_ENTRY_PROMPTS = {
    "gap": GAP_ENTRY_PROMPT,
    "cosmic_duality": COSMIC_ENTRY_PROMPT,
    "vibrational_anchor": ANCHOR_ENTRY_PROMPT,
}
_PATTERN_AUTO_PROMPTS = {
    "gap": GAP_AUTO_PROMPT,
    "cosmic_duality": COSMIC_AUTO_PROMPT,
    "vibrational_anchor": ANCHOR_AUTO_PROMPT,
}


def _claude(system, prompt, client):
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2400,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = next((b.text for b in response.content if b.type == "text"), "")
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            return json.loads(m.group())
        raise ValueError(f"No valid JSON in Claude response:\n{text[:400]}")


def _pick_pattern(processed: dict) -> str:
    """Rotate through patterns so each appears roughly equally."""
    import random
    recent = [v.get("pattern") for v in list(processed.values())[-6:] if v.get("pattern")]
    counts = {p: recent.count(p) for p in ("gap", "cosmic_duality", "vibrational_anchor")}
    min_count = min(counts.values())
    candidates = [p for p, c in counts.items() if c == min_count]
    return random.choice(candidates)


def generate_carousel_from_note(note, config, client, pattern: str):
    system = SYSTEM.format(**{k: config.get(k, "") for k in ("voice", "visual_style", "philosophy")})
    prompt = _PATTERN_ENTRY_PROMPTS[pattern].format(title=note["title"], content=note["content"])
    return _claude(system, prompt, client)


def auto_generate_carousel(notes, config, client, pattern: str):
    import random
    system = SYSTEM.format(**{k: config.get(k, "") for k in ("voice", "visual_style", "philosophy")})
    if notes:
        samples = random.sample(notes, min(6, len(notes)))
        context = "\n\n---\n\n".join(f"[{n['title']}]\n{n['content'][:400]}" for n in samples)
        prompt = _PATTERN_AUTO_PROMPTS[pattern].format(context=context)
    else:
        prompt = EMPTY_VAULT_PROMPTS[pattern]
    return _claude(system, prompt, client)


# ── Caption builder ────────────────────────────────────────────────────────

def build_caption(result):
    caption = result.get("caption", "").strip()
    hashtags = " ".join(f"#{h.lstrip('#')}" for h in result.get("hashtags", []))
    if hashtags:
        return f"{caption}\n\n.\n.\n.\n{hashtags}"
    return caption


# ── Phase 1: Generate content + slides ────────────────────────────────────

def phase1(generate_if_empty=False, dry_run=False):
    config = load_config()
    processed = load_processed()
    notes = get_notes(config)
    unprocessed = [n for n in notes if n["id"] not in processed]

    note = None
    auto_mode = False

    if unprocessed:
        note = unprocessed[0]
        print(f"📝  Note: {note['title']}")
    elif generate_if_empty:
        print("📝  No new notes — auto-generating from vault themes...")
        auto_mode = True
    else:
        print("✅  No new notes to process.")
        return

    # Claude
    api_key = os.environ.get("ANTHROPIC_API_KEY") or config.get("anthropic_api_key", "")
    if not api_key:
        print("❌  ANTHROPIC_API_KEY not set.")
        sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key)

    pattern = _pick_pattern(processed)
    print(f"⚡  Generating carousel content via Claude (pattern: {pattern})...")
    if auto_mode:
        result = auto_generate_carousel(notes, config, client, pattern)
        note = {
            "id": f"auto_{datetime.now().strftime('%Y%m%d_%H%M')}",
            "title": result.get("_title", "Auto Generated"),
            "content": result.get("_raw_content", ""),
        }
    else:
        result = generate_carousel_from_note(note, config, client, pattern)
    result["pattern"] = pattern

    caption_text = build_caption(result)

    # Generate 7 unique AI background images — one per slide
    print("🎨  Generating 7 background images via Replicate (Flux)...")
    from image_gen import generate_slide_images
    bg_bytes_list = generate_slide_images(result.get("image_prompt", ""), config, n_slides=7)

    # Build all 7 carousel slides with Pillow
    print("🖼️  Building 7 carousel slides...")
    slug = re.sub(r"[^\w]", "_", note["title"].lower())[:40].strip("_") or "post"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_dir = OUTPUT_DIR / f"{timestamp}_{slug}"

    from carousel_maker import build_carousel
    slide_paths = build_carousel(result, bg_bytes_list, config, out_dir)

    # Save supporting files
    (out_dir / "caption.txt").write_text(caption_text, encoding="utf-8")
    (out_dir / "content.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    # Relative paths (forward slashes for raw.githubusercontent.com URLs)
    rel_slides = [p.relative_to(BASE_DIR).as_posix() for p in slide_paths]

    # Save pending plan for phase 2
    plan = {
        "note_id": note["id"],
        "note_title": note["title"],
        "output_dir": out_dir.relative_to(BASE_DIR).as_posix(),
        "slide_files": rel_slides,
        "caption": caption_text,
        "generated_at": datetime.now().isoformat(),
        "dry_run": dry_run,
    }
    PENDING_PATH.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"💾  Saved: {out_dir.name}/")
    if dry_run:
        print("\n🔍  DRY RUN — slides generated. Skipping Instagram post.")
        print(f"\nCaption preview:\n{caption_text[:300]}...")
    else:
        print("📋  Plan saved — waiting for git push, then run --phase2")

    # Mark processed immediately (prevents double-generation)
    processed[note["id"]] = {
        "title": note["title"],
        "pattern": pattern,
        "generated_at": datetime.now().isoformat(),
        "dry_run": dry_run,
        "output": out_dir.relative_to(BASE_DIR).as_posix(),
    }
    save_processed(processed)


# ── Phase 2: Post carousel to Instagram ───────────────────────────────────

def phase2():
    if not PENDING_PATH.exists():
        print("❌  No pending plan found (.pending_plan.json missing). Run --phase1 first.")
        sys.exit(1)

    plan = json.loads(PENDING_PATH.read_text(encoding="utf-8"))

    if plan.get("dry_run"):
        print("🔍  DRY RUN plan — nothing to post.")
        PENDING_PATH.unlink(missing_ok=True)
        return

    # Build raw.githubusercontent.com URLs
    # GITHUB_REPOSITORY = "owner/repo", GITHUB_REF_NAME = "main"
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    branch = os.environ.get("GITHUB_REF_NAME", "main")

    if not repo:
        print("❌  GITHUB_REPOSITORY not set. This phase must run inside GitHub Actions.")
        print("    For local testing, use --phase1 --dry-run instead.")
        sys.exit(1)

    base_url = f"https://raw.githubusercontent.com/{repo}/{branch}"
    image_urls = [f"{base_url}/{rel}" for rel in plan["slide_files"]]

    print(f"📸  Posting {len(image_urls)}-slide carousel to Instagram...")
    for i, url in enumerate(image_urls, 1):
        print(f"    Slide {i}: .../{url.split('/')[-1]}")

    config = load_config()
    ig_user_id = os.environ.get("INSTAGRAM_USER_ID") or config.get("instagram_user_id", "")
    ig_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN") or config.get("instagram_access_token", "")

    if not ig_user_id or not ig_token:
        print("❌  INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN required.")
        sys.exit(1)

    from instagram import post_carousel
    ig_result = post_carousel(image_urls, plan["caption"], ig_user_id, ig_token)
    print(f"✅  Live! Post ID: {ig_result.get('id')}")
    print(f"    Note: {plan['note_title']}")

    # Clean up pending plan
    PENDING_PATH.unlink(missing_ok=True)


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram carousel pipeline")
    parser.add_argument("--phase1", action="store_true", help="Generate content + slides")
    parser.add_argument("--phase2", action="store_true", help="Post carousel to Instagram")
    parser.add_argument("--dry-run", action="store_true", help="Phase 1 only, no Instagram post")
    parser.add_argument("--generate-if-empty", action="store_true", help="Auto-generate if no new notes")
    args = parser.parse_args()

    if args.phase2:
        phase2()
    elif args.phase1 or args.dry_run or args.generate_if_empty:
        phase1(generate_if_empty=args.generate_if_empty, dry_run=args.dry_run)
    else:
        parser.print_help()
