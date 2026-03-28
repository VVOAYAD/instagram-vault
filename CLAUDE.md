# Claude — Project Context

## Who I am
Non-technical content creator. Consciousness, nervous system reprogramming, human transformation. I call my insights "downloads and reflections." I post to Instagram as @alvvoayadcreates.

My philosophy: never explain the tree. Transmit. Transfer with feeling, not information.

## How to work with me
- Give me direct orders, I don't need hand-holding
- I'm not technical — explain things simply when needed
- I work across multiple projects, all living in this vault

## My projects

### 1. Instagram Automation (LIVE)
Fully automated 7-slide carousel pipeline. Posts daily at 9am UTC to @alvvoayadcreates.
- GitHub: https://github.com/VVOAYAD/instagram-vault
- Instagram User ID: 17841472919301425
- Facebook Page ID: 1095552560298097
- Meta App ID: 866371822870634
- To trigger manually: `gh workflow run "Daily Instagram Post" --repo VVOAYAD/instagram-vault`
- Token renewal due: ~late May 2026 (see Projects/Instagram Automation/Token renewal.md)

### 2. SQU Financial Dashboard
Built yesterday. GitHub: https://github.com/VVOAYAD/squ-financial-dashboard

### 3. Oman Lifestyle Hub
In progress. GitHub: https://github.com/VVOAYAD/oman-lifestyle-hub
Next session: continue building it out.

## Key file locations
| File | What it does |
|---|---|
| `Downloads/` | Notes for Instagram — one .md file = one post |
| `config.json` | Voice, style, post time, handle |
| `pipeline.py` | The automation engine |
| `carousel_maker.py` | Builds the 7 slides |
| `.github/workflows/daily_post.yml` | Schedule (cron) |
| `Projects/` | Notes about each project |
| `Journal/` | Private writing, never posted |

## GitHub CLI
Installed at: `/c/Program Files/GitHub CLI/gh`
Always use: `export PATH="$PATH:/c/Program Files/GitHub CLI"`
Authenticated as: VVOAYAD

## Python
Located at: `C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`
Not on PATH — use full path for local runs

## Important rules
- Instagram token expires every 60 days — remind me when due
- Repo must stay Public (Instagram needs to fetch carousel images from it)
- Downloads/ folder notes get auto-posted. Journal/ notes never do.
