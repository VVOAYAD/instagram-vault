"""
Daily Instagram carousel generator — Alvvo Ayad.

Two phases (matches daily_post.yml):
  python post.py --generate   # plan + create 7 slides into output/YYYY-MM-DD/
  python post.py --post       # publish that day's slides to Instagram

One aesthetic (aesthetic.md) — injected verbatim into every image prompt.
One image model — Gemini 2.5 Flash Image (nano-banana), text baked into art.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import random
import sys
from pathlib import Path

import requests
from google import genai
from google.genai import types

import instagram

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
AESTHETIC_PATH = ROOT / "aesthetic.md"
KB_PATH = ROOT / "knowledge_base.md"
OUTPUT_DIR = ROOT / "output"
STATE_PATH = ROOT / ".last_post.json"

GITHUB_REPO = "VVOAYAD/instagram-vault"
GITHUB_BRANCH = "main"

IMAGE_MODEL = "gemini-3.1-flash-image-preview"  # Nano Banana 2
TEXT_MODEL = "gemini-2.5-flash"
INSPO_DIR = ROOT / "style_refs"
INSPO_COUNT = 6  # reference images sent with every slide call (max 14)

# Weekly domain rotation — one per day of week. Monday = weekday 0.
DOMAINS = [
    "Nervous system & trauma",        # Monday
    "Consciousness & presence",       # Tuesday
    "Shadow & self",                  # Wednesday
    "Embodiment",                     # Thursday
    "Philosophy & wisdom",            # Friday
    "Energy & reiki",                 # Saturday
    "Becoming & integration",         # Sunday
]

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["gemini_api_key"] = os.environ.get("GEMINI_API") or cfg.get("gemini_api_key", "")
    cfg["instagram_user_id"] = os.environ.get("INSTAGRAM_USER_ID") or cfg.get("instagram_user_id", "")
    cfg["instagram_access_token"] = (
        os.environ.get("INSTAGRAM_ACCESS_TOKEN") or cfg.get("instagram_access_token", "")
    )
    return cfg


def load_aesthetic() -> str:
    return AESTHETIC_PATH.read_text(encoding="utf-8")


def pick_domain(today: dt.date) -> str:
    """Monday = DOMAINS[0], Sunday = DOMAINS[6]."""
    return DOMAINS[today.weekday()]


def load_kb() -> dict[str, list[str]]:
    """Parse knowledge_base.md into {domain_key: [insights...]}.

    Domain headers are lines like '## MONDAY — Nervous system & trauma'.
    Insights are numbered lines '1. [tag] The insight text.'
    Tag brackets are stripped so Gemini never sees teacher names.
    """
    text = KB_PATH.read_text(encoding="utf-8")
    domains: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("## ") and "—" in line:
            current = line.split("—", 1)[1].strip()
            domains[current] = []
            continue
        if current and line and line[0].isdigit() and ". " in line[:5]:
            body = line.split(". ", 1)[1].strip()
            if body.startswith("[") and "]" in body:
                body = body.split("]", 1)[1].strip()
            if body:
                domains[current].append(body)
    return domains


def pick_insights(domain_key: str, kb: dict[str, list[str]], seed: int, n: int = 5) -> list[str]:
    """Pick n insights from the domain — deterministic per day."""
    pool = kb.get(domain_key, [])
    if not pool:
        return []
    rng = random.Random(seed + 2)
    return rng.sample(pool, k=min(n, len(pool)))


def plan_carousel(client: genai.Client, domain: str, insights: list[str], aesthetic: str) -> dict:
    """Alvvo as coach/healer/wise sister — carousel seeded by today's domain insights."""
    seed_block = "\n".join(f"- {ins}" for ins in insights) if insights else "(no seeds)"
    prompt = f"""You are writing a 7-slide Instagram carousel for @alvvoayadcreates.

WHO ALVVO IS:
A guide. Not a guru. Not a therapist. A wise older sister who survived the
things she teaches and remembers exactly how it felt. She writes for hurting,
awakening people — mostly 20s-30s — who are tired of surface-level self-help
and starving for something that actually lands.

HER VOICE:
- Human, warm, direct. She talks the way a close friend talks at 2am.
- She names what's hard without flinching. No toxic positivity.
- She's spiritual but never mystical. She's awake but never above.
- She respects the reader's intelligence. No hand-holding, no guru voice.
- When she teaches a practice, it's specific and doable tonight.
- When she witnesses pain, she names the exact shape of it.

NEVER USE these (they sound like AI spiritual slop):
- "vessel", "frequency", "alignment", "source", "portal", "rise", "awaken"
- "you are enough", "you are light", "trust the process", "divine feminine"
- "regulate your vessel", "shift your story", "reclaim your power"
- Step 1/Step 2/Step 3 language (unless a real method genuinely fits)
- Empty rhetorical questions
- Anything a ChatGPT spiritual coach would say

NEVER INVENT SPECIFIC TECHNIQUES. Alvvo is NOT a somatic therapist or biohacker.
Do NOT suggest: ice baths, cold water, tapping (EFT), specific breathwork patterns
(4-7-8, box breathing, Wim Hof), journaling prompts, gratitude lists, vagus nerve
hacks, supplements, specific yoga poses, hot/cold exposure, or any other branded
technique. If the reader needs those, a specialist gives them.

NEVER name-drop teachers or authors. The insights below are Alvvo's absorbed
understanding. Write them as if they are her own lived clarity. Do not say
"According to van der Kolk" or "Tolle says" or similar. No citations, no quotes.

What Alvvo CAN guide (universal awareness moves that belong to everyone):
Noticing · pausing · naming the pattern · slowing down · feeling without
fixing · witnessing with compassion · choosing a different response · asking
honest questions · being with discomfort · letting something be true.

TODAY'S DOMAIN: {domain}

TODAY'S SEED INSIGHTS (Alvvo's absorbed wisdom — do NOT credit, use as your
own ground; you can paraphrase, combine, or extend them, but stay faithful
to their meaning):
{seed_block}

Build the 7-slide carousel from these seeds. Pick the angle that makes the
strongest, clearest post — don't try to fit every seed in. One clear thread.

HOW THE CAROUSEL CAN SHAPE-SHIFT (pick what serves THIS post):
- TEACHING: name the pattern most people live in → offer a specific different move
- WITNESSING: name the exact hidden pain → explain why it's there → offer the truth
- RECLAMATION: name the lie they were taught → name the actual truth → invite them to live it
- CONFESSION: speak a hard truth most people won't say out loud, then hold the reader
- MIRROR: show them the behavior they do → name what's underneath it → offer what to do instead

SLIDE RULES:
- Slide 1: The hook. Stops the scroll. 4-10 words. Can be ALL CAPS.
- Slides 2-6: Take them somewhere real. Mix reframe + universal practice + emotional truth. Under 18 words per slide. Plain English.
- Slide 7: Land them softly. One line. Human, grounded, kind. Not a CTA, not a slogan.

Return ONLY valid JSON:
{{
  "slide_1_hook": "the hook",
  "slide_2": "slide 2 text",
  "slide_3": "slide 3 text",
  "slide_4": "slide 4 text",
  "slide_5": "slide 5 text",
  "slide_6": "slide 6 text",
  "slide_7_cta": "the soft landing",
  "caption": "Instagram caption under 220 chars. Natural human voice, like texting one friend. Zero mystical jargon. End with 3-5 hashtags on a new line."
}}"""
    resp = client.models.generate_content(
        model=TEXT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.9,
        ),
    )
    return json.loads(resp.text)


def build_image_prompt(slide_text: str, role: str, aesthetic: str) -> str:
    role_hints = {
        "hook": "text rendered as ALL CAPS, wide letter-spacing, chrome or gold fill, subtle glow, dominant focal point",
        "body": "text rendered as italic serif (Cormorant-style), soft, romantic, lower third of frame, small relative to art",
        "cta": "text rendered as ALL CAPS, wide letter-spacing, chrome/gold, centered, luminous",
    }
    return f"""{aesthetic}

The reference images attached show the exact visual vibe — match their palette,
composition, texture, and mood. Draw from the same world they live in.

Generate a 4:5 vertical (1080x1350) Instagram carousel slide in that visual world.

TEXT TO RENDER INSIDE THE IMAGE (exact wording, no changes, no extra text): "{slide_text}"
TEXT STYLE: {role_hints[role]}

The text must be integrated into the artwork — same grain, same lighting, same
painted texture. NOT a clean overlay. NOT photorealistic. Painted, illustrated,
grainy, cohesive with the reference images."""


def load_inspo_refs(seed: int) -> list[types.Part]:
    """Pick a deterministic subset of aesthetic inspo images to feed as style refs."""
    if not INSPO_DIR.exists():
        return []
    images = sorted(p for p in INSPO_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not images:
        return []
    rng = random.Random(seed)
    picks = rng.sample(images, k=min(INSPO_COUNT, len(images)))
    parts = []
    for p in picks:
        mime = "image/jpeg" if p.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    return parts


def generate_slide(client: genai.Client, prompt: str, refs: list[types.Part]) -> bytes:
    """Call nano-banana, return PNG bytes of the first image part."""
    contents = [*refs, prompt] if refs else prompt
    resp = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                data = inline.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                return data
    raise RuntimeError(f"No image returned by {IMAGE_MODEL}")


def generate_all(cfg: dict) -> None:
    if not cfg["gemini_api_key"]:
        sys.exit("GEMINI_API not set")

    client = genai.Client(api_key=cfg["gemini_api_key"])
    today = dt.date.today()
    seed = today.toordinal()
    domain = pick_domain(today)
    kb = load_kb()
    insights = pick_insights(domain, kb, seed, n=5)
    aesthetic = load_aesthetic()

    print(f"→ domain: {domain}")
    print(f"→ seeds: {len(insights)} insights from KB")

    plan = plan_carousel(client, domain, insights, aesthetic)
    print(f"→ hook: {plan['slide_1_hook']}")

    slides = [
        ("hook", plan["slide_1_hook"]),
        ("body", plan["slide_2"]),
        ("body", plan["slide_3"]),
        ("body", plan["slide_4"]),
        ("body", plan["slide_5"]),
        ("body", plan["slide_6"]),
        ("cta", plan["slide_7_cta"]),
    ]

    day_dir = OUTPUT_DIR / today.isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    refs = load_inspo_refs(seed)
    print(f"→ style refs: {len(refs)} images (driving the vibe)")

    for i, (role, text) in enumerate(slides, 1):
        prompt = build_image_prompt(text, role, aesthetic)
        print(f"  slide {i}/7 — {role} — {text[:60]}")
        png = generate_slide(client, prompt, refs)
        (day_dir / f"slide_{i}.png").write_bytes(png)

    STATE_PATH.write_text(
        json.dumps(
            {"date": today.isoformat(), "caption": plan["caption"], "domain": domain},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"✓ 7 slides saved to {day_dir}")


def publish(cfg: dict) -> None:
    if not (cfg["instagram_user_id"] and cfg["instagram_access_token"]):
        sys.exit("INSTAGRAM_USER_ID or INSTAGRAM_ACCESS_TOKEN not set")

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    day = state["date"]
    urls = [
        f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/output/{day}/slide_{i}.png"
        for i in range(1, 8)
    ]

    # sanity check — fetch first slide so a missing CDN fails fast
    r = requests.head(urls[0], timeout=15, allow_redirects=True)
    if r.status_code != 200:
        sys.exit(f"slide URL not reachable yet: {urls[0]} ({r.status_code})")

    print(f"→ posting carousel for {day}")
    result = instagram.post_carousel(
        image_urls=urls,
        caption=state["caption"],
        user_id=cfg["instagram_user_id"],
        access_token=cfg["instagram_access_token"],
    )
    print(f"✓ posted: {result}")


def plan_only(cfg: dict) -> None:
    """Print the day's 7-slide text plan without generating images (free)."""
    if not cfg["gemini_api_key"]:
        sys.exit("GEMINI_API not set")
    client = genai.Client(api_key=cfg["gemini_api_key"])
    today = dt.date.today()
    seed = today.toordinal()
    domain = pick_domain(today)
    kb = load_kb()
    insights = pick_insights(domain, kb, seed, n=5)
    aesthetic = load_aesthetic()
    print(f"domain ({today.strftime('%A')}): {domain}")
    print(f"seeds:")
    for s in insights:
        print(f"  · {s}")
    print()
    plan = plan_carousel(client, domain, insights, aesthetic)
    for i in range(1, 8):
        key = "slide_1_hook" if i == 1 else "slide_7_cta" if i == 7 else f"slide_{i}"
        print(f"  {i}. {plan[key]}")
    print(f"\ncaption:\n{plan['caption']}")


def main() -> None:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--generate", action="store_true")
    g.add_argument("--post", action="store_true")
    g.add_argument("--plan", action="store_true", help="text only, no images, no cost")
    args = p.parse_args()

    cfg = load_config()
    if args.generate:
        generate_all(cfg)
    elif args.post:
        publish(cfg)
    else:
        plan_only(cfg)


if __name__ == "__main__":
    main()
