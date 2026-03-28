#!/usr/bin/env python3
"""
journal_to_content.py — Mine journal entries for Instagram-ready downloads.

Reads Brain/Journal/ entries, sends to Claude, extracts post-worthy insights,
writes them as .md files to the Downloads/ folder for the pipeline to pick up.

Usage:
  python journal_to_content.py              # process all new journal entries
  python journal_to_content.py --all        # reprocess everything (ignore history)
  python journal_to_content.py --dry-run    # show what would be generated, don't write
  python journal_to_content.py --limit 20  # only look at the 20 most recent entries
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

import anthropic

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
PROCESSED_PATH = BASE_DIR / ".journal_processed.json"
JOURNAL_DIR = Path("C:/Users/Administrator/Brain/Journal")
DOWNLOADS_DIR = BASE_DIR / "Downloads"

VOICE_AND_PHILOSOPHY = """
VOICE: Deep, precise, and transmission-based. Speaks from the body, not the mind.
Short sentences. No filler. Each word earns its place.
Topics: nervous system, conditioning, beliefs, consciousness, regulation, reprogramming.
But never from textbooks — always from felt experience.
The reader finishes a post and FEELS something shift, not just thinks something new.

PHILOSOPHY: Never explain the tree. Never post branches.
Each piece carries the full feeling on its own.
Find the engine. Express it in different forms.
Transfer with absolute feeling, not stop-scrolls.
The goal is not to inform — it is to shift.

WHAT NOT TO DO:
- Explain instead of transmit
- Add filler words or motivational fluff
- Post something that sounds like everyone else
- Use lists where a sentence would hit harder
- Post from the head instead of the body
"""

EXTRACT_PROMPT = """You are reading raw private journal entries from a consciousness and nervous system teacher.
Your job: identify moments in these entries that carry real transmission potential — insights, felt realizations,
raw truths, or turning points that could become Instagram carousel content.

Here are the journal entries:

{entries}

Extract 2-5 Instagram "downloads" from these entries.
Each download is a seed — a central transmission that can be turned into a 7-slide carousel.

Rules:
- Pull from actual content in the entries — don't invent
- The best downloads are often the short, raw, declarative ones
- They should feel true, not polished
- Transmit the emotion, not just the idea
- Skip anything that's a to-do list, task, or purely logistical

Return ONLY valid JSON — an array of download objects:
[
  {{
    "title": "Short title (3-6 words, how you'd name the .md file)",
    "content": "The raw download — 2-6 sentences that carry the full transmission. Write in the creator's voice, from the felt experience, not as a summary.",
    "source_hint": "Brief note on which entry this came from (e.g. '2026-03-26 entry')",
    "why_it_works": "1 sentence on why this has transmission potential"
  }}
]

If there is nothing post-worthy in these entries, return an empty array: []
"""


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


def get_journal_entries(limit=None, skip_processed=True):
    """Read journal entries from Brain/Journal/."""
    if not JOURNAL_DIR.exists():
        print(f"❌  Journal directory not found: {JOURNAL_DIR}")
        return []

    processed = load_processed() if skip_processed else {}

    entries = []
    paths = sorted(JOURNAL_DIR.glob("*.md"), reverse=True)  # newest first
    if limit:
        paths = paths[:limit]

    for path in paths:
        if path.name.startswith(".") or path.name in ("How to use this.md",):
            continue
        if skip_processed and path.name in processed:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if len(text) < 30:  # skip near-empty files
            continue
        entries.append({"filename": path.name, "content": text, "path": str(path)})

    return entries


def chunk_entries(entries, chunk_size=10):
    """Group entries into batches to avoid huge prompts."""
    for i in range(0, len(entries), chunk_size):
        yield entries[i : i + chunk_size]


def extract_downloads(entries, client, dry_run=False):
    """Send a batch of entries to Claude and get back download seeds."""
    combined = "\n\n---\n\n".join(
        f"[{e['filename']}]\n{e['content']}" for e in entries
    )

    prompt = EXTRACT_PROMPT.format(entries=combined)

    if dry_run:
        print(f"\n📖  Would send {len(entries)} entries to Claude for analysis.")
        return []

    print(f"🤖  Analysing {len(entries)} entries...", end=" ", flush=True)

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=f"You extract Instagram content from private journal entries.\n{VOICE_AND_PHILOSOPHY}",
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()

    # strip markdown code fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    downloads = json.loads(raw)
    print(f"found {len(downloads)} downloads.")
    return downloads


def slugify(title):
    """Convert title to a safe filename."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "_", slug.strip())
    slug = re.sub(r"_+", "_", slug)
    return slug[:60]


def write_download(download, downloads_dir, dry_run=False):
    """Write a download seed to the Downloads folder."""
    title = download["title"]
    content = download["content"]
    filename = f"{slugify(title)}.md"
    path = downloads_dir / filename

    if path.exists():
        print(f"   ⚠️   Skipped (already exists): {filename}")
        return None

    md = f"# {title}\n\n{content}\n"

    if dry_run:
        print(f"\n   [DRY RUN] Would write: {filename}")
        print(f"   Source: {download.get('source_hint', '?')}")
        print(f"   Why: {download.get('why_it_works', '?')}")
        print(f"   Content preview: {content[:100]}...")
        return filename

    path.write_text(md, encoding="utf-8")
    print(f"   ✅  {filename}")
    print(f"       Source: {download.get('source_hint', '?')}")
    return filename


def main():
    parser = argparse.ArgumentParser(description="Mine journal entries for Instagram downloads")
    parser.add_argument("--all", action="store_true", help="Reprocess all entries (ignore history)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without writing")
    parser.add_argument("--limit", type=int, default=None, help="Only look at N most recent entries")
    args = parser.parse_args()

    config = load_config()
    api_key = config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌  No ANTHROPIC_API_KEY found in config or environment.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    DOWNLOADS_DIR.mkdir(exist_ok=True)

    entries = get_journal_entries(
        limit=args.limit,
        skip_processed=not args.all,
    )

    if not entries:
        print("✅  No new journal entries to process.")
        return

    print(f"📔  Found {len(entries)} journal entries to analyse.")

    processed = load_processed()
    all_written = []

    for i, batch in enumerate(chunk_entries(entries, chunk_size=8)):
        print(f"\n🗂️   Batch {i + 1} ({len(batch)} entries):")
        downloads = extract_downloads(batch, client, dry_run=args.dry_run)

        for d in downloads:
            written = write_download(d, DOWNLOADS_DIR, dry_run=args.dry_run)
            if written:
                all_written.append(written)

        # mark batch as processed
        if not args.dry_run:
            for e in batch:
                processed[e["filename"]] = datetime.utcnow().isoformat()
            save_processed(processed)

    print(f"\n🎉  Done! {len(all_written)} new downloads written to {DOWNLOADS_DIR}")
    if all_written and not args.dry_run:
        print("\n📋  Files ready for the pipeline:")
        for f in all_written:
            print(f"    • {f}")
        print("\nRun the daily post workflow to pick one up, or trigger manually:")
        print("  gh workflow run 'Daily Instagram Post' --repo VVOAYAD/instagram-vault")


if __name__ == "__main__":
    main()
