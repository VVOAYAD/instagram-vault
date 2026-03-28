# Instagram Automation

A fully automated carousel pipeline. Write a note → it posts to @alvvoayadcreates daily at 9am UTC. No manual triggering needed.

## How it works
1. Write a note in the `Downloads/` folder in Obsidian
2. Obsidian Git syncs it to GitHub automatically
3. Every day at 9am GitHub runs the pipeline:
   - Claude reads your note and writes 7 carousel slides
   - Replicate generates an AI background image
   - Pillow builds all 7 slides
   - Instagram posts the carousel automatically

## GitHub repo
https://github.com/VVOAYAD/instagram-vault

## How to trigger a post manually
Go to github.com/VVOAYAD/instagram-vault → Actions → Daily Instagram Post → Run workflow

## API keys (stored in GitHub Secrets)
- Anthropic (Claude) — console.anthropic.com
- Replicate (images) — replicate.com/account/billing
- Instagram token — expires every 60 days, see "Token Renewal" note

## Files that matter
- `config.json` — change your voice, style, post time, Instagram handle
- `Downloads/` — your notes go here, one .md file = one post
- `.github/workflows/daily_post.yml` — change `0 9 * * *` to change post time
