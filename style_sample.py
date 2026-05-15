"""Two-sample gate generator.
Loads refs from styles/<style>/ and generates 2 samples in that exact style.
No text overlay. Pure visual fidelity test.

Usage:
  python style_sample.py --style retro_futurism
  python style_sample.py --style retro_futurism --count 3
"""
from __future__ import annotations
import argparse, base64, datetime as dt, os, sys, time
from pathlib import Path
from google import genai
from google.genai import types

ROOT = Path(__file__).parent
STYLES_ROOT = ROOT / "styles"
OUT_ROOT = Path(r"C:\Users\Administrator\Desktop\instagram system samples")
IMAGE_MODEL = "gemini-3.1-flash-image-preview"  # Nano Banana 2 — Alvvo's pick (2026-05-05)

env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API = os.environ.get("GEMINI_API")
if not API:
    print("ERROR: GEMINI_API missing in .env"); sys.exit(1)

# Per-sample subjects so the 2 samples aren't identical
SUBJECTS = [
    "a single human figure mid-action, emotionally charged moment",
    "an iconic object or symbol, hero shot, dramatic mood",
]

DNA_PROMPT = (
    "Vertical 4:5 image. Match the visual style of the reference images EXACTLY — "
    "same palette, same texture, same rendering technique, same composition language, "
    "same mood, same overall feel. The refs ARE the source of truth for the aesthetic. "
    "Subject: {subject}. "
    "DO NOT include any text, captions, watermarks, or signatures. NO TEXT in the image."
)


def load_refs(style: str) -> list[types.Part]:
    folder = STYLES_ROOT / style
    if not folder.exists():
        print(f"ERROR: style folder missing: {folder}"); sys.exit(1)
    imgs = sorted(p for p in folder.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not imgs:
        print(f"ERROR: no images in {folder}"); sys.exit(1)
    parts = []
    for p in imgs:
        mime = "image/jpeg" if p.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    print(f"  loaded {len(parts)} refs from styles/{style}/")
    return parts


def gen_one(client, refs, subject: str) -> bytes | None:
    prompt = DNA_PROMPT.format(subject=subject)
    contents = [*refs, prompt]
    resp = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="4:5"),
        ),
    )
    for cand in resp.candidates or []:
        for part in cand.content.parts or []:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                d = inline.data
                return base64.b64decode(d) if isinstance(d, str) else d
    return None


def main():
    global IMAGE_MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", required=True)
    ap.add_argument("--post", required=True, help="post number, e.g. 1")
    ap.add_argument("--count", type=int, default=2)
    ap.add_argument("--model", default=IMAGE_MODEL, help="override image model")
    args = ap.parse_args()
    IMAGE_MODEL = args.model

    out = OUT_ROOT / str(args.post) / "samples"
    out.mkdir(parents=True, exist_ok=True)
    print(f"style: {args.style}  |  post: {args.post}")
    print(f"out:   {out}")

    client = genai.Client(api_key=API)
    refs = load_refs(args.style)

    for i in range(1, args.count + 1):
        subject = SUBJECTS[(i - 1) % len(SUBJECTS)]
        print(f"[sample {i}] subject: {subject[:60]}...")
        try:
            data = gen_one(client, refs, subject)
        except Exception as e:
            print(f"  ERROR: {e}"); continue
        if not data:
            print(f"  no image returned"); continue
        path = out / f"sample_{i:02d}.png"
        path.write_bytes(data)
        print(f"  -> {path}")
        time.sleep(1)


if __name__ == "__main__":
    main()
