"""
Reel Intelligence pipeline — Alvvo AI IG project.

Pipeline:
  URL -> yt-dlp download -> ffmpeg audio + keyframes
       -> faster-whisper transcript (local, free)
       -> Tesseract OCR on keyframes (local, free)
       -> Claude Haiku 4.5 structured synthesis (~$0.002/reel)
       -> Markdown note in vault Inbox/

Usage:
  python reel_ingest.py <reel_url>
  python reel_ingest.py <reel_url> --keep-frames
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Auto-load .env so ANTHROPIC_API_KEY is available without a parent shell sourcing it.
try:
    from dotenv import load_dotenv
    for env_path in [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

FFMPEG = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
VAULT_ROOT = Path(r"C:\Users\Administrator\Desktop\Second Brain")
WORK_DIR = Path(r"C:\Users\Administrator\reel_intake")

# bucket -> vault folder for filed analyses
BUCKETS = {
    "art": VAULT_ROOT / "Projects" / "Instagram Automation" / "Inbox" / "Reels",
    "edu": VAULT_ROOT / "Projects" / "alvvo.ai" / "Inbox" / "Reels",
}
DEFAULT_BUCKET = "art"

WHISPER_MODEL = "base"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"


def slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[-\s]+", "-", s)[:60] or "reel"


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def download(url: str, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    template = str(out_dir / "reel.%(ext)s")
    info_template = str(out_dir / "reel")
    run(["yt-dlp", "-o", template, "--write-info-json", "-o", f"infojson:{info_template}", url], check=True)
    info_path = out_dir / "reel.info.json"
    info = json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
    video = next((p for p in out_dir.glob("reel.*") if p.suffix in {".mp4", ".webm", ".mkv"}), None)
    if not video:
        raise RuntimeError("yt-dlp did not produce a video file")
    return {"video": video, "info": info}


def extract_audio(video: Path) -> Path:
    audio = video.with_suffix(".wav")
    run([FFMPEG, "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)], check=True)
    return audio


def extract_keyframes(video: Path, every_seconds: int = 3) -> list[Path]:
    frames_dir = video.parent / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir()
    run([FFMPEG, "-y", "-i", str(video), "-vf", f"fps=1/{every_seconds},scale=720:-1", "-q:v", "3",
         str(frames_dir / "f_%03d.jpg")], check=True)
    return sorted(frames_dir.glob("f_*.jpg"))


def transcribe(audio: Path) -> str:
    from faster_whisper import WhisperModel
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(audio), beam_size=1, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()


def ocr_frames(frames: list[Path]) -> list[str]:
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = TESSERACT
    out: list[str] = []
    seen: set[str] = set()
    for f in frames:
        text = pytesseract.image_to_string(Image.open(f)).strip()
        text = re.sub(r"\s+", " ", text)
        if text and text not in seen and len(text) > 5:
            seen.add(text)
            out.append(text)
    return out


SYNTH_PROMPT_BASE = """You are the Reel Intelligence engine for Alvvo Ayad's content empire.
Alvvo creates content on consciousness, nervous-system reprogramming, patterns, and human transformation.
He saves reels he likes so we can reverse-engineer what works.

Output ONE strict JSON object (no prose, no fences) with these fields:
{
  "creator": "uploader handle/name",
  "duration_sec": number,
  "hook": "the first 3 seconds — visual + verbal — what stops the scroll",
  "payload": "the actual lesson/idea/value delivered, in 1-2 sentences",
  "structure": "hook | setup | demo | proof | CTA pattern in 1 line",
  "voice": "delivery style (e.g. 'casual selfie + bro pacing + swears for emphasis')",
  "cta": "exact CTA the creator used",
  "visual_dna": "palette + typography + motion + framing in 1 line — what makes it visually distinct",
  "niche_tags": ["3-6 tags"],
  "steal_worthy": "what's reusable for Alvvo — 1 specific tactic, frame, or hook formula",
  "risk_or_avoid": "anything off-brand (or 'none')",
  "score": "1-10 how relevant to Alvvo's empire",
  "one_line_summary": "what this reel IS in 12 words or less"
}
"""

BUCKET_HINTS = {
    "art": "Bucket: ART. Lens = visual aesthetic, motifs, palette, typography, motion language. Score for visual inspiration value.",
    "edu": "Bucket: EDUCATIONAL. Lens = teaching structure, hook formula, mental model, retention device. Score for teaching power.",
}


def synthesize(transcript: str, ocr_lines: list[str], info: dict, bucket: str) -> dict:
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set (expected in instagram_system/.env)")
    client = anthropic.Anthropic(api_key=api_key)
    payload = {
        "url": info.get("webpage_url"),
        "uploader": info.get("uploader"),
        "uploader_id": info.get("uploader_id"),
        "duration": info.get("duration"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "caption": info.get("description"),
        "audio_transcript": transcript,
        "on_screen_text": ocr_lines,
    }
    user_msg = (
        BUCKET_HINTS.get(bucket, "")
        + "\n\nReturn ONLY the JSON object — no prose, no markdown fences.\n\nInputs:\n"
        + json.dumps(payload, ensure_ascii=False)
    )
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        system=SYNTH_PROMPT_BASE,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    # Some models still wrap output — clip to the outermost JSON object if needed.
    if not raw.startswith("{"):
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if m:
            raw = m.group(0)
    return json.loads(raw)


def write_note(synth: dict, info: dict, transcript: str, ocr_lines: list[str], bucket: str) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    handle_raw = info.get("uploader_id") or info.get("uploader") or "creator"
    handle = re.sub(r"[^\w.-]", "_", handle_raw)
    slug = slugify(synth.get("one_line_summary") or info.get("title") or "reel")
    folder = BUCKETS.get(bucket, BUCKETS[DEFAULT_BUCKET]) / today
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{handle}--{slug}.md"
    tag_list = ", ".join(synth.get("niche_tags", []))
    body = f"""---
type: reel-intelligence
bucket: {bucket}
date: {today}
url: {info.get("webpage_url", "")}
creator: {info.get("uploader", "")}
handle: {info.get("uploader_id", "")}
duration_sec: {info.get("duration", "")}
likes: {info.get("like_count", "")}
comments: {info.get("comment_count", "")}
score: {synth.get("score", "")}
tags: [{tag_list}]
---

# {synth.get("one_line_summary", "Reel")}

**Hook:** {synth.get("hook", "")}

**Payload:** {synth.get("payload", "")}

**Structure:** {synth.get("structure", "")}

**Voice:** {synth.get("voice", "")}

**Visual DNA:** {synth.get("visual_dna", "")}

**CTA:** {synth.get("cta", "")}

**Steal-worthy for Alvvo:** {synth.get("steal_worthy", "")}

**Risk / avoid:** {synth.get("risk_or_avoid", "")}

---

## Caption
{info.get("description", "") or "(none)"}

## Audio transcript
{transcript or "(none)"}

## On-screen text
{chr(10).join(f"- {l}" for l in ocr_lines) if ocr_lines else "(none)"}
"""
    path.write_text(body, encoding="utf-8")
    return path


def write_payload(work: Path, info: dict, transcript: str, ocr_lines: list[str], bucket: str, frames: list[Path]) -> Path:
    """Dump everything Claude Code needs to do the synth itself — no API call."""
    payload = {
        "bucket": bucket,
        "url": info.get("webpage_url"),
        "uploader": info.get("uploader"),
        "uploader_id": info.get("uploader_id"),
        "duration": info.get("duration"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "caption": info.get("description"),
        "audio_transcript": transcript,
        "on_screen_text": ocr_lines,
        "frames": [str(f) for f in frames],
        "synth_prompt": SYNTH_PROMPT_BASE,
        "bucket_hint": BUCKET_HINTS.get(bucket, ""),
    }
    p = work / "payload.json"
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def ingest(url: str, bucket: str = DEFAULT_BUCKET, keep_frames: bool = True, use_api: bool = False) -> dict:
    """Run the pipeline. By default skips the LLM step — Claude Code does the synth itself.
    Pass use_api=True to call Claude Haiku via the Anthropic API (requires credit balance)."""
    if bucket not in BUCKETS:
        raise ValueError(f"bucket must be one of {list(BUCKETS)}")
    work = WORK_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"[1/4] download    -> {work}")
    dl = download(url, work)
    video, info = dl["video"], dl["info"]
    print(f"        creator: {info.get('uploader')} | duration: {info.get('duration')}s")

    print("[2/4] audio + frames")
    audio = extract_audio(video)
    frames = extract_keyframes(video)

    print(f"[3/4] transcribe  ({len(frames)} frames, {audio.stat().st_size//1024} KB audio)")
    transcript = transcribe(audio)
    print(f"        {len(transcript)} chars transcript")

    print("[4/4] OCR")
    ocr_lines = ocr_frames(frames)
    print(f"        {len(ocr_lines)} unique on-screen text blocks")

    synth: dict = {}
    if use_api:
        print(f"[+]   Claude Haiku synthesis (bucket={bucket})")
        try:
            synth = synthesize(transcript, ocr_lines, info, bucket)
        except Exception as e:
            print(f"        synth failed ({e}) — Claude Code will synth instead")

    payload_path = write_payload(work, info, transcript, ocr_lines, bucket, frames)
    note = write_note(synth, info, transcript, ocr_lines, bucket)
    print(f"\n[stub] {note}")
    print(f"[data] {payload_path}")
    print(f"[work] {work}   <-- frames here")
    if not synth:
        print("[next] Claude Code: read payload.json + frames, write final synth into the stub note.")
    if not keep_frames:
        shutil.rmtree(work, ignore_errors=True)
    return {"note_path": note, "payload_path": payload_path, "work_dir": work, "synth": synth, "info": info}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--bucket", choices=list(BUCKETS), default=DEFAULT_BUCKET)
    ap.add_argument("--no-keep-frames", action="store_true", help="delete work dir after run (default: keep)")
    ap.add_argument("--use-api", action="store_true", help="call Claude Haiku via Anthropic API (requires credit)")
    args = ap.parse_args()
    ingest(args.url, bucket=args.bucket, keep_frames=not args.no_keep_frames, use_api=args.use_api)
    return 0


if __name__ == "__main__":
    sys.exit(main())
