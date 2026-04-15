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
Wise older sister / coach. Warm, direct, human. Teaches by naming patterns + offering awareness. No mystical jargon ("vessel", "frequency", "portal" are banned). No invented techniques (ice, tapping, breathwork methods — Alvvo doesn't teach those). Only universal awareness moves: notice, pause, feel, witness, name, slow down.

## Themes (30, rotating by day of year)
philosophy · nervous system · patterns & habits · people-pleasing & boundaries · overthinking · self-worth · sovereignty & business · growth · shadow & trauma

## Cost
~$0.35–0.70 per carousel, ~$10–15/month daily. Gemini API billing enabled, $5 budget alert set.

## Improvements
*(add your ideas here)*

## Last session — 2026-04-15
- FULL REBUILD. Deleted ~17 bloat files, 4 dirs. One pipeline: `post.py`.
- Switched image gen to Nano Banana 2 → text baked into art, no more PIL overlays.
- Built `aesthetic.md` + copied 34 inspo images to `style_refs/` (fed to model per slide).
- Dialed voice: wise sister coach, no mystical jargon, no invented techniques.
- Expanded themes from 8 to 30 (practical growth topics, not just philosophy).
- Added `--plan` mode for free tone-testing.
- Billing enabled on Gemini API, $5 budget alert set.
- First live generate ran clean. Aesthetic + voice both locked.

## Next step
- Monitor first few daily auto-posts in IG feed — check how nano-banana text reads on mobile
- If visual variety needs a boost, add pattern rotation (The Gap / The Descent / The Mirror)
- Add new themes anytime by editing the THEMES list in `post.py`

---
*Update "Last session" and "Next step" above at the end of every session.*
