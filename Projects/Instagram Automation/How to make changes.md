# How to make changes

Everything is editable from Obsidian. Edit → save → Obsidian Git pushes it to GitHub automatically.

---

## Change post time

Open: `.github/workflows/daily_post.yml`
Find: `- cron: '0 9 * * *'`

The format is `minute hour * * *`. Change the hour (UTC):
- 5am UTC = 9am Oman/UAE
- 9am UTC = 1pm Oman/UAE
- 6am UTC = 10am Oman/UAE

---

## Change your voice or style

Open: `config.json`
Edit the `voice`, `visual_style`, or `philosophy` fields.

---

## Change your Instagram handle shown on slides

Open: `config.json`
Edit `instagram_handle` — currently `@alvvoayadcreates`

---

## Write a note to post

Create a `.md` file in `Downloads/` → write your raw download → save.
It gets posted on the next 9am UTC run (or trigger manually).

See: [[Downloads/.how_to_write|How to write a download]]

---

## Trigger a post right now (without waiting for 9am)

Go to: https://github.com/VVOAYAD/instagram-vault/actions
Click **Daily Instagram Post** → **Run workflow** → **Run workflow**

---

## Skip a day

No new notes = system auto-generates from your existing vault themes. Nothing to do.

---

## Add a new carousel pattern

Open a Claude Code session → say "add a new carousel pattern called [name]" → describe the visual style.

---

## Current carousel patterns

1. **The Gap** — slow, expansive, one thought per slide deepening into the body
2. **The Cosmic Duality** — single words across 4 slides building to one devastating sentence
3. **The Vibrational Anchor** — direct, rhythmic, grounding permission slips

---

## What's automated (never touch these)

- The API calls (Claude, Replicate, Instagram)
- Building the slides
- Committing images to GitHub
- Posting to Instagram
