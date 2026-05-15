# Instagram Automation — @alvvoayadcreates

## What this is
Fully automated 7-slide carousel pipeline. Posts daily at 9am UTC.
GitHub: https://github.com/VVOAYAD/instagram-vault

## Key IDs
- Instagram User ID: 17841472919301425
- Facebook Page ID: 1095552560298097
- Meta App ID: 866371822870634
- IG token renewal due: late May 2026

## Key files (lean stack)
| File | What it does |
|---|---|
| `post.py` | The whole pipeline — generate / post / plan |
| `aesthetic.md` | Locked visual DNA (palettes, motifs, typography) |
| `style_refs/` | 34 inspo images, 6 fed to nano-banana per slide for style consistency |
| `config.json` | Handle, post time (secrets live in GitHub Secrets, not here) |
| `instagram.py` | Meta Graph API poster |
| `.github/workflows/daily_post.yml` | Cron at 9am UTC |

## Model
- Image: **Gemini 3.1 Flash Image Preview (Nano Banana 2)** — text baked inside the art
- Text plan: **Gemini 2.5 Flash** — free tier is enough

## Trigger manually
```
export PATH="$PATH:/c/Program Files/GitHub CLI"
gh workflow run "Daily Instagram Post" --repo VVOAYAD/instagram-vault
```

## Test tone locally (FREE — text only, no image cost)
```
PYTHONIOENCODING=utf-8 GEMINI_API="your_key" python post.py --plan
```

## Rules
- Repo must stay Public — Instagram fetches images from raw.githubusercontent.com
- Never commit API keys. Secrets live in GitHub Actions Secrets only.
- IG access token expires every 60 days — next due late May 2026

## Voice
Wise older sister / coach. Warm, direct, human. **Scientific spine** — name the mechanism in PLAIN ENGLISH (not clinical Latin), name the pattern it produces, give the move. Same warmth, harder edge. No inspirational-poster phrasing — Alvvo said the old copy was "bloat and bad and generic" (2026-05-04).

Slide structure: (1) mechanism in plain English, (2) pattern it produces, (3) interrupt/move. Short. No fluff.

Scientific = SPECIFIC concrete description, not vocabulary. Bad: "your dorsal vagal branch is freeze-coded." Good: "your body learned to go still when affection felt unsafe."

Banned clinical terms (translate, don't use): polyvagal, sympathetic/parasympathetic, default mode network, interoception, IFS, allostatic load, fawn response, attachment styles (use these concepts but in everyday language).

Banned words/phrases: "vessel", "frequency", "portal", vague intransitive verbs (become/emerge/radiate/align/flow without a specific referent), rhetorical questions with obvious answers, anything a Pinterest graphic would say.

No invented techniques (ice, tapping, breathwork — Alvvo doesn't teach those). Only universal awareness moves: notice, pause, feel, witness, name, slow down.

## Themes (30, rotating by day of year)
philosophy · nervous system · patterns & habits · people-pleasing & boundaries · overthinking · self-worth · sovereignty & business · growth · shadow & trauma

## Cost
~$0.35–0.70 per carousel, ~$10–15/month daily. Gemini API billing enabled, $5 budget alert set.

## Improvements
*(add your ideas here)*

## Last session — 2026-05-04
- Reel-ingest pipeline hardened (`reel_ingest.py`): routes art→instagram_system, edu→alvvo.ai, uses Gemini 2.5 Flash for synthesis.
- Telegram bot BLOCKED by Oman ISP (TCP-reset on api.telegram.org). Bot code complete, can't deploy. Two paths: proxy config or pivot to Discord/email bridge.
- Aesthetic rebuild: 5+ iterations, no lock yet. Discovered fallenpoet uses split-panel diptychs + ALL-CAPS condensed sans — not painted oil portraits. Built `split_carousel.py`.
- Voice updated: scientific = plain-English specificity, clinical Latin terms now banned (translate them).
- New workflow: `styles/<name>/` folder system. Rotates between style folders. Two-sample gate before any full run.
- Copy voice corrected: "bloat and bad and generic" → scientific but plain-English. No clinical jargon.

## Next step
- Alvvo drops ONE anchor image showing the exact look he wants (not a grid, one image). From that rebuild the generator.
- After visual lock: rewrite `post.py` copy prompts with new scientific-but-plain-English voice.
- Telegram: decide Discord vs email vs web-page bridge.

---
*Update "Last session" and "Next step" above at the end of every session.*
