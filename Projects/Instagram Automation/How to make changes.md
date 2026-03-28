# How to make changes

Everything is editable from Obsidian. Edit → save → Obsidian Git pushes it to GitHub.

## Change post time
Open: `instagram_system/.github/workflows/daily_post.yml`
Find: `- cron: '0 9 * * *'`
The number after 0 is the hour in UTC. 9 = 9am UTC.
- UTC +4 (UAE/Oman) → 9am UTC = 1pm local, 5am UTC = 9am local

## Change your voice or style
Open: `instagram_system/config.json`
Edit the `voice`, `visual_style`, or `philosophy` fields

## Change your Instagram handle shown on slides
Open: `instagram_system/config.json`
Edit `instagram_handle`

## Add a note to post
Create a new .md file in `Downloads/` folder — that's it

## Skip a day
Just don't have any new notes and the system auto-generates from your existing vault themes
