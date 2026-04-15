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
OUTPUT_DIR = ROOT / "output"
STATE_PATH = ROOT / ".last_post.json"

GITHUB_REPO = "VVOAYAD/instagram-vault"
GITHUB_BRANCH = "main"

IMAGE_MODEL = "gemini-3.1-flash-image-preview"  # Nano Banana 2
TEXT_MODEL = "gemini-2.5-flash"
INSPO_DIR = ROOT / "style_refs"
INSPO_COUNT = 6  # reference images sent with every slide call (max 14)

THEMES = [
    # philosophy & consciousness
    "consciousness as a felt sense, not a concept",
    "knowing thyself — the permanent self beneath the conditioning",
    "becoming — the version of you that already exists",

    # nervous system & body
    "nervous system regulation — the body before the belief",
    "anxiety as old protection, not a warning about now",
    "feeling your feelings instead of managing them",

    # patterns & habits
    "noticing the patterns you keep repeating in relationships",
    "why the same kind of person keeps showing up in your life",
    "breaking a habit that numbs you instead of heals you",
    "the small daily choices that are actually shaping you",
    "how your avoidance is costing you the thing you want",

    # people-pleasing & boundaries
    "people-pleasing is self-abandonment with a smile",
    "the cost of being 'the nice one'",
    "saying no without explaining yourself",
    "when being understanding is actually betraying yourself",

    # overthinking & mind
    "overthinking is avoidance dressed as responsibility",
    "the thoughts you keep on repeat are not all yours",
    "stop negotiating with your inner critic",

    # self-worth & self-abandonment
    "self-worth as something you are, not something you earn",
    "you don't need to perform to deserve rest",
    "the version of love that needs you to shrink is not love",

    # sovereignty & business
    "standing on business — sovereignty, discernment, not shrinking",
    "discipline is love. motivation is a mood.",
    "charging your worth without apologizing for it",

    # growth & evolution
    "growth is unglamorous — the grief of outgrowing who you were",
    "expansion — holding more without collapsing",
    "letting the old version of you die without flinching",
    "why healing feels like losing everything at first",

    # shadow & trauma
    "your triggers are teachers, not enemies",
    "what you reject in others is usually exiled in you",
    "the trauma response you've been calling your personality",
]

PALETTES = [
    "chrome_navy: liquid silver figures on deep navy starfield, pink+gold glitter stars",
    "electric_airbrush: electric blue + saturated red, high-gloss airbrush, chrome highlights",
    "y2k_romance: pastel pink, chrome silver, sky blue with clouds, heart motifs",
    "dreamcore_blur: magenta and acid green, soft blurred gradient, heavy grain",
    "celestial_warmth: amber, violet, starburst white, painterly sky",
    "retro_anime: jewel tones, gold sparkle, cel-shaded 90s anime",
]

MOTIFS = [
    "chrome liquid metal figure with luminous halo",
    "tribal chrome ornament floating in sky with clouds",
    "metallic angel with glowing wings, mountains far below",
    "4-point sparkles and prismatic lens flares across the frame",
    "starburst explosion at center with nebula backdrop",
    "90s cel-shaded anime hands holding glowing objects",
    "lone silhouette in vast painted landscape",
    "glitching marble statue with chromatic aberration",
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


def pick_theme(today: dt.date) -> str:
    return THEMES[today.toordinal() % len(THEMES)]


def pick_palette_and_motif(seed: int) -> tuple[str, str]:
    rng = random.Random(seed)
    return rng.choice(PALETTES), rng.choice(MOTIFS)


def plan_carousel(client: genai.Client, theme: str, aesthetic: str) -> dict:
    """Alvvo as coach/healer/wise sister — writes carousels that make people feel AND know."""
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

What Alvvo CAN guide (universal awareness moves that belong to everyone):
- Noticing what you feel, where it lives in the body
- Pausing before reacting
- Naming the pattern out loud
- Slowing down
- Feeling without fixing
- Witnessing yourself with compassion
- Choosing a different response
- Asking yourself honest questions
- Being with discomfort
- Letting something be true

HOW THE CAROUSEL CAN SHAPE-SHIFT (pick what serves THIS theme):
- TEACHING: name the pattern most people live in → offer a specific different move
- WITNESSING: name the exact hidden pain → explain why it's there → offer the truth
- RECLAMATION: name the lie they were taught → name the actual truth → invite them to live it
- CONFESSION: speak a hard truth most people won't say out loud, then hold the reader
- MIRROR: show them the behavior they do → name what's underneath it → offer what to do instead

Pick the shape that serves the theme — don't force every post into the same mold.

SLIDE RULES:
- Slide 1: The hook. Stops the scroll. Names something most people don't say out loud. 4-10 words. Can be ALL CAPS.
- Slides 2-6: Take them somewhere real. Mix reframe + specific practice + emotional truth. Each slide earns its place. Under 18 words per slide. Plain English.
- Slide 7: Land them softly. One line. Human, grounded, kind. Not a CTA, not a slogan.

Theme for this post: {theme}

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


def build_image_prompt(slide_text: str, role: str, palette: str, motif: str, aesthetic: str) -> str:
    role_hints = {
        "hook": "text rendered as ALL CAPS, wide letter-spacing, chrome or gold fill, subtle glow, dominant focal point",
        "body": "text rendered as italic serif (Cormorant-style), soft, romantic, lower third of frame, small relative to art",
        "cta": "text rendered as ALL CAPS, wide letter-spacing, chrome/gold, centered, luminous",
    }
    return f"""{aesthetic}

Generate a 4:5 vertical (1080x1350) Instagram carousel slide.

PALETTE: {palette}
MOTIF: {motif}
TEXT TO RENDER INSIDE THE IMAGE (exact wording, no changes, no extra text): "{slide_text}"
TEXT STYLE: {role_hints[role]}

The text must be integrated into the artwork — same grain, same lighting, same
painted texture. NOT a clean overlay. NOT photorealistic. Painted, illustrated,
grainy, Y2K chrome-core, cosmic dreamcore mood."""


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
    theme = pick_theme(today)
    palette, motif = pick_palette_and_motif(today.toordinal())
    aesthetic = load_aesthetic()

    print(f"→ theme: {theme}")
    print(f"→ palette: {palette.split(':')[0]}")
    print(f"→ motif: {motif}")

    plan = plan_carousel(client, theme, aesthetic)
    print(f"→ plan: {plan['slide_1_hook']}")

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

    refs = load_inspo_refs(today.toordinal())
    print(f"→ style refs: {len(refs)} images from aesthetic inspo")

    for i, (role, text) in enumerate(slides, 1):
        prompt = build_image_prompt(text, role, palette, motif, aesthetic)
        print(f"  slide {i}/7 — {role} — {text[:60]}")
        png = generate_slide(client, prompt, refs)
        (day_dir / f"slide_{i}.png").write_bytes(png)

    STATE_PATH.write_text(
        json.dumps(
            {"date": today.isoformat(), "caption": plan["caption"], "theme": theme},
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
    theme = pick_theme(today)
    aesthetic = load_aesthetic()
    print(f"theme: {theme}\n")
    plan = plan_carousel(client, theme, aesthetic)
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
