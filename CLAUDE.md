# Claude — Project Context

## Who I am
Non-technical content creator. Consciousness, nervous system reprogramming, human transformation. I call my insights "downloads and reflections." I post to Instagram as @alvvoayadcreates.

My philosophy: never explain the tree. Transmit. Transfer with feeling, not information.

## How to work with me
- Give me direct orders, I don't need hand-holding
- I'm not technical — explain things simply when needed
- I work across multiple projects

## My Brain vault (second brain)
Location: `C:\Users\Administrator\Brain\`
Synced via: Obsidian Sync (across all devices including iPhone)

**At the start of every session: read the Brain vault to get full context.**
The vault contains notes on all projects, journal entries, philosophy, and downloads.

Structure:
- `Brain/Home.md` — start here for overview
- `Brain/Projects/` — notes on each project
- `Brain/Downloads/` — spiritual downloads queued for Instagram
- `Brain/Journal/` — private writing
- `Brain/Resources/My Voice and Philosophy.md` — voice, style, philosophy

> Note: Claude reads local files only. Brain vault is synced from Obsidian cloud to local machine
> automatically when Obsidian is open. Open Obsidian before starting a Claude session if notes
> were added from phone.

## My projects

### 1. Instagram Automation (LIVE)
Fully automated 7-slide carousel pipeline. Posts daily at 9am UTC to @alvvoayadcreates.
- Code: `C:\Users\Administrator\instagram_system\`
- GitHub: https://github.com/VVOAYAD/instagram-vault
- Instagram User ID: 17841472919301425
- Facebook Page ID: 1095552560298097
- Meta App ID: 866371822870634
- To trigger manually: `gh workflow run "Daily Instagram Post" --repo VVOAYAD/instagram-vault`
- Token renewal due: ~late May 2026

### 2. SQU Financial Dashboard
GitHub: https://github.com/VVOAYAD/squ-financial-dashboard

### 3. Oman Lifestyle Hub
In progress. GitHub: https://github.com/VVOAYAD/oman-lifestyle-hub

## Instagram automation — key files
| File | What it does |
|---|---|
| `instagram_system/Downloads/` | Notes for Instagram — one .md file = one post |
| `instagram_system/config.json` | Voice, style, post time, handle |
| `instagram_system/pipeline.py` | The automation engine |
| `instagram_system/carousel_maker.py` | Builds the 7 slides |
| `instagram_system/.github/workflows/daily_post.yml` | Schedule (cron: 9am UTC) |

## Visual aesthetic (LOCKED — always apply this)
User's aesthetic: illustrated/painted/collage, NOT photorealistic 3D renders.
- Deep jewel tones: navy blue, deep purple, rich teal
- Textures: brushstrokes, grain, film texture, glitter, gold foil
- Alien Affirmation specifically: illustrated green alien, deep navy starfield, scattered glitter stars
- All Flux prompts must include "illustrated art style, textured, NOT photorealistic"
- Text on Alien Affirmation: ALL CAPS with wide letter tracking (spaces between chars)
- "Simple and plain ain't me" — always layer, texture, and depth

## Carousel patterns (rotate automatically — 6 total)
1. The Gap — slow, expansive, deepens into the body
2. The Cosmic Duality — single words across 4 slides → devastating sentence
3. The Vibrational Anchor — direct, grounding, rhythmic
4. The Alien Affirmation — full image, ALL CAPS tracked text, one affirmation per slide
5. The Anime Meme — full image, centered subtitle-style caption per slide
6. The Scripture Card — ornate border frame, sacred concept header, 7 reflections

## Pattern references (auto-learning system)
Folder: `instagram_system/pattern_references/`
- Drop screenshots of posts you like into this folder
- Run `python learn_pattern.py` to add them to the rotation
- Learned patterns live in `learned_patterns.json`
- At start of session: check if new images are in pattern_references/ that haven't been processed yet

## GitHub CLI
Installed at: `/c/Program Files/GitHub CLI/gh`
Always use: `export PATH="$PATH:/c/Program Files/GitHub CLI"`
Authenticated as: VVOAYAD

## Python
Located at: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`
Not on PATH — use full path for local runs

## Important rules
- Instagram token expires every 60 days — next due late May 2026
- Repo must stay Public (Instagram fetches carousel images from raw.githubusercontent.com)
- Downloads/ notes get auto-posted. Journal/ notes never do.
