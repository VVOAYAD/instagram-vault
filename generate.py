#!/usr/bin/env python3
"""
Instagram Content Automation System
────────────────────────────────────
Add entries to vault.md, then run this script to generate:
  - Polished Instagram captions
  - Ready-to-paste Midjourney prompts
  - Typographic image files

Usage:
  python generate.py                  # Interactive — pick from vault
  python generate.py --latest         # Process newest vault entry
  python generate.py --auto           # AI generates a fresh insight
  python generate.py --entry "Mirror" # Process specific entry (keyword match)
  python generate.py --queue 7        # Generate a week of content
  python generate.py --list           # List all vault entries
  python generate.py --no-image       # Skip image creation
"""

import anthropic
import json
import re
import sys
import argparse
import hashlib
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
VAULT_PATH = BASE_DIR / "vault.md"
CONFIG_PATH = BASE_DIR / "config.json"
OUTPUT_DIR = BASE_DIR / "output"
PROCESSED_PATH = BASE_DIR / ".processed.json"

# ── Config & State ────────────────────────────────────────────────────────

def load_config():
    if not CONFIG_PATH.exists():
        print("❌  config.json not found.")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg

def load_processed():
    if PROCESSED_PATH.exists():
        with open(PROCESSED_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_processed(data):
    with open(PROCESSED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_client(config):
    api_key = config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌  API key missing. Set 'anthropic_api_key' in config.json or ANTHROPIC_API_KEY env var.")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)

# ── Vault Parser ──────────────────────────────────────────────────────────

def parse_vault():
    """Parse vault.md → list of entry dicts."""
    if not VAULT_PATH.exists():
        print(f"❌  vault.md not found at {VAULT_PATH}")
        return []

    text = VAULT_PATH.read_text(encoding="utf-8")
    entries = []

    for section in re.split(r"\n(?=## )", text):
        lines = section.strip().split("\n")
        if not lines or not lines[0].startswith("## "):
            continue

        title_line = lines[0][3:].strip()

        # Optional [YYYY-MM-DD]
        date_match = re.search(r"\[(\d{4}-\d{2}-\d{2})\]", title_line)
        if date_match:
            date = date_match.group(1)
            title = title_line.replace(f"[{date}]", "").strip(" -–")
        else:
            date = datetime.now().strftime("%Y-%m-%d")
            title = title_line

        # Body up to --- separator
        body_lines = []
        for line in lines[1:]:
            if re.match(r"^---+\s*$", line.strip()):
                break
            body_lines.append(line)

        content = "\n".join(body_lines).strip()
        if not content or "Add Your Next Download" in content:
            continue

        entry_id = hashlib.md5(f"{title}::{content[:80]}".encode()).hexdigest()[:12]
        entries.append({"id": entry_id, "title": title, "date": date, "content": content})

    return entries

# ── Content Generation ────────────────────────────────────────────────────

SYSTEM_TEMPLATE = """You are the content engine for a thought leader in consciousness, nervous system reprogramming, and human transformation.

VOICE:
{voice}

VISUAL AESTHETIC:
{visual_style}

CONTENT PHILOSOPHY:
{philosophy}

Core rule: Never explain. Never over-describe. Transmit. Each post should feel like something the reader already knew but couldn't articulate until now."""

ENTRY_PROMPT = """Transform this raw download into Instagram content.

DOWNLOAD TITLE: {title}
RAW CONTENT:
{content}

Return ONLY valid JSON — no explanation, no markdown fences:
{{
  "caption_main": "The core transmission. 1–3 lines. This is what stops the scroll. No emojis unless they serve the feeling. No filler.",
  "caption_body": "2–3 lines that deepen without explaining. Expand the feeling, don't decode it.",
  "caption_cta": "One line. A question or invitation to reflect — not a call to action.",
  "overlay_line1": "Primary image text — maximum 9 words",
  "overlay_line2": "Second image line — maximum 9 words, or empty string if not needed",
  "overlay_line3": "Third image line — maximum 7 words, or empty string",
  "midjourney_prompt": "Complete Midjourney v6.1 prompt. Dark, minimal, ethereal, abstract, consciousness-themed. NO text in image. Match the aesthetic in config. End with: --ar 1:1 --v 6.1 --style raw",
  "hashtags": ["10", "niche", "hashtags", "no", "hash", "symbol", "mix", "of", "broad", "niche"],
  "content_type": "quote OR insight OR framework OR question",
  "feeling_note": "The emotional frequency this post carries — 1 short line"
}}"""

AUTO_PROMPT = """Study these existing downloads from my vault:

{context}

Generate ONE completely original download that:
- Has NOT been said in these examples
- Expands the field in a new direction
- Carries the same transmission quality and nervous-system frequency
- Is polished enough to post immediately

Return ONLY valid JSON:
{{
  "title": "Name or concept for this insight",
  "raw_content": "The full download — 3–6 potent sentences. Raw and real.",
  "caption_main": "Core Instagram transmission — 1–3 lines",
  "caption_body": "2–3 lines of depth",
  "caption_cta": "Reflection invitation",
  "overlay_line1": "Main image text (max 9 words)",
  "overlay_line2": "Second image line (max 9 words or empty string)",
  "overlay_line3": "Third line (max 7 words or empty string)",
  "midjourney_prompt": "Complete Midjourney v6.1 prompt — dark, minimal, ethereal, abstract --ar 1:1 --v 6.1 --style raw",
  "hashtags": ["10", "hashtags", "no", "hash", "symbol"],
  "feeling_note": "The frequency"
}}"""


def _call_claude(system, user, client):
    """Single Claude call with adaptive thinking, returns parsed JSON."""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1800,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = next((b.text for b in response.content if b.type == "text"), "")
    return _parse_json(text)


def _parse_json(text):
    """Extract JSON from Claude response robustly."""
    # Strip markdown fences if present
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except Exception as e:
            raise ValueError(f"JSON parse failed: {e}\n\nRaw:\n{text[:600]}")
    raise ValueError(f"No JSON found in response:\n{text[:400]}")


def generate_from_entry(entry, config, client):
    system = SYSTEM_TEMPLATE.format(
        voice=config.get("voice", ""),
        visual_style=config.get("visual_style", ""),
        philosophy=config.get("philosophy", ""),
    )
    prompt = ENTRY_PROMPT.format(title=entry["title"], content=entry["content"])
    return _call_claude(system, prompt, client)


def auto_generate(config, client, n_samples=6):
    entries = parse_vault()
    if not entries:
        print("Vault is empty — add downloads to vault.md first.")
        sys.exit(1)

    import random
    samples = random.sample(entries, min(n_samples, len(entries)))
    context = "\n\n---\n\n".join(
        f"[{e['title']}]\n{e['content'][:500]}" for e in samples
    )

    system = SYSTEM_TEMPLATE.format(
        voice=config.get("voice", ""),
        visual_style=config.get("visual_style", ""),
        philosophy=config.get("philosophy", ""),
    )
    return _call_claude(system, AUTO_PROMPT.format(context=context), client)

# ── Output ────────────────────────────────────────────────────────────────

def save_output(title, result, image_path=None):
    """Save all generated content to an output subfolder."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s]+", "_", slug)[:40].strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    folder = OUTPUT_DIR / f"{timestamp}_{slug}"
    folder.mkdir(exist_ok=True)

    # JSON dump
    (folder / "content.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Formatted caption
    hashtags = " ".join(f"#{h}" for h in result.get("hashtags", []))
    caption = "\n".join([
        result.get("caption_main", ""),
        "",
        result.get("caption_body", ""),
        "",
        result.get("caption_cta", ""),
        "",
        ".",
        ".",
        ".",
        hashtags,
    ])
    (folder / "caption.txt").write_text(caption.strip(), encoding="utf-8")

    # Midjourney prompt
    (folder / "midjourney_prompt.txt").write_text(
        result.get("midjourney_prompt", ""), encoding="utf-8"
    )

    # Copy image
    if image_path and Path(image_path).exists():
        import shutil
        shutil.copy(image_path, folder / "image.png")

    return folder


def print_result(result, folder=None):
    """Pretty-print results to terminal."""
    bar = "─" * 64

    print(f"\n{bar}")
    print("  🖼   IMAGE OVERLAY TEXT")
    print(bar)
    for key in ("overlay_line1", "overlay_line2", "overlay_line3"):
        val = result.get(key, "").strip()
        if val:
            print(f"  {val}")

    print(f"\n{bar}")
    print("  ✍️   CAPTION")
    print(bar)
    print(result.get("caption_main", ""))
    print()
    print(result.get("caption_body", ""))
    print()
    print(result.get("caption_cta", ""))
    hashtags = " ".join(f"#{h}" for h in result.get("hashtags", []))
    print(f"\n.\n.\n.\n{hashtags}")

    print(f"\n{bar}")
    print("  🎨  MIDJOURNEY PROMPT  (copy → paste into Discord)")
    print(bar)
    print(result.get("midjourney_prompt", ""))

    print(f"\n{bar}")
    print(f"  🔮  Feeling:  {result.get('feeling_note', '')}")
    print(f"  📁  Type:     {result.get('content_type', '')}")
    if folder:
        print(f"  💾  Saved:    {folder}")
    print(bar)

# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Instagram Content Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--latest", action="store_true", help="Process newest vault entry")
    parser.add_argument("--auto", action="store_true", help="AI generates a fresh insight")
    parser.add_argument("--entry", type=str, metavar="KEYWORD", help="Process entry matching keyword")
    parser.add_argument("--queue", type=int, metavar="N", help="Generate N posts in sequence")
    parser.add_argument("--list", action="store_true", help="List all vault entries")
    parser.add_argument("--no-image", action="store_true", help="Skip image creation")
    args = parser.parse_args()

    config = load_config()

    # --list doesn't need API
    if args.list:
        entries = parse_vault()
        if not entries:
            print("Vault is empty — add entries to vault.md")
            return
        processed = load_processed()
        print(f"\n{'#':<4} {'TITLE':<42} {'DATE':<12} STATUS")
        print("─" * 72)
        for i, e in enumerate(entries, 1):
            status = "✅ done" if e["id"] in processed else "⬜ new"
            print(f"{i:<4} {e['title'][:40]:<42} {e['date']:<12} {status}")
        new_count = sum(1 for e in entries if e["id"] not in processed)
        print(f"\n  {new_count} unprocessed / {len(entries)} total")
        return

    client = get_client(config)
    entries = parse_vault()

    def _make_image(result, title):
        if args.no_image:
            return None
        try:
            from image_maker import create_image
            lines = [result.get(f"overlay_line{i}", "") for i in (1, 2, 3)]
            lines = [l for l in lines if l.strip()]
            return create_image(lines, title, config)
        except Exception as e:
            print(f"⚠️  Image creation skipped: {e}")
            return None

    # ── --auto ───────────────────────────────────────────────────────────
    if args.auto:
        print("\n🤖  Auto-generating from vault themes...")
        result = auto_generate(config, client)
        title = result.get("title", "auto_generated")
        image_path = _make_image(result, title)
        folder = save_output(title, result, image_path)
        print_result(result, folder)

        answer = input("\n➕  Add this to vault.md? (y/n): ").strip().lower()
        if answer == "y":
            with open(VAULT_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n\n## {title}\n\n{result.get('raw_content', result.get('caption_main', ''))}\n\n---\n")
            print("✅  Added to vault.md")
        return

    # ── --queue ──────────────────────────────────────────────────────────
    if args.queue:
        processed = load_processed()
        unprocessed = [e for e in entries if e["id"] not in processed]
        count = min(args.queue, len(unprocessed))
        if count == 0:
            print("All entries already processed. Use --auto to generate fresh content.")
            return
        print(f"\n📅  Generating {count} posts...")
        saved = []
        for i, entry in enumerate(unprocessed[:count], 1):
            print(f"\n[{i}/{count}] {entry['title']}")
            try:
                result = generate_from_entry(entry, config, client)
                image_path = _make_image(result, entry["title"])
                folder = save_output(entry["title"], result, image_path)
                processed[entry["id"]] = {
                    "title": entry["title"],
                    "generated_at": datetime.now().isoformat(),
                    "folder": str(folder),
                }
                save_processed(processed)
                saved.append((entry["title"], folder))
                print(f"  ✅  {folder.name}")
            except Exception as ex:
                print(f"  ❌  Error: {ex}")

        print(f"\n✅  Generated {len(saved)} posts in {OUTPUT_DIR}")
        return

    # ── Single entry ──────────────────────────────────────────────────────
    if not entries:
        print("Vault is empty — add entries to vault.md first.")
        return

    selected = None

    if args.entry:
        keyword = args.entry.lower()
        matches = [e for e in entries if keyword in e["title"].lower()]
        if not matches:
            print(f"No entry matching '{args.entry}'")
            sys.exit(1)
        selected = matches[0]
        print(f"Found: {selected['title']}")

    elif args.latest:
        selected = entries[-1]
        print(f"Latest entry: {selected['title']}")

    else:
        # Interactive
        processed = load_processed()
        new_entries = [e for e in entries if e["id"] not in processed]
        done_entries = [e for e in entries if e["id"] in processed]

        print("\n📔  VAULT ENTRIES — unprocessed\n")
        if not new_entries:
            print("  All entries processed! Use --auto for fresh content.")
            return

        for i, e in enumerate(new_entries, 1):
            print(f"  [{i}] {e['title']}  ({e['date']})")

        if done_entries:
            print(f"\n  ({len(done_entries)} already generated — use --list to see all)")

        choice = input("\nEnter number (Enter = 1): ").strip()
        idx = int(choice) - 1 if choice.isdigit() else 0
        selected = new_entries[max(0, min(idx, len(new_entries) - 1))]

    print(f"\n⚡  Generating: {selected['title']}")
    result = generate_from_entry(selected, config, client)
    image_path = _make_image(result, selected["title"])
    folder = save_output(selected["title"], result, image_path)

    processed = load_processed()
    processed[selected["id"]] = {
        "title": selected["title"],
        "generated_at": datetime.now().isoformat(),
        "folder": str(folder),
    }
    save_processed(processed)

    print_result(result, folder)


if __name__ == "__main__":
    main()
