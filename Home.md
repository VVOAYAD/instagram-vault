# Home

Welcome back. Everything you need is here.

---

## Write a new post

Go to `Downloads/` → create a new note → write your download.
The pipeline picks it up automatically at **9am UTC daily**.

> Don't overthink the note. Write the raw transmission. Claude does the rest.

**Template:** [[Downloads/.how_to_write|How to write a download]]

---

## Projects

- [[Projects/Instagram Automation/What this is|Instagram Automation]] — automated posting to @alvvoayadcreates
- [[Projects/SQU Financial Dashboard/Overview|SQU Financial Dashboard]]
- [[Projects/Oman Lifestyle Hub/Overview|Oman Lifestyle Hub]]

---

## My voice

[[Resources/My Voice and Philosophy|My Voice & Philosophy]] — what I stand for, how I sound

---

## Journal

Private writing lives in `Journal/`. Never posted, never synced to GitHub.
Write freely here — no one sees it but you.

---

## Quick actions

| What | How |
|------|-----|
| Trigger a post now | [GitHub Actions](https://github.com/VVOAYAD/instagram-vault/actions) → Run workflow |
| Change post time | Edit `.github/workflows/daily_post.yml` — line: `cron: '0 9 * * *'` |
| Change voice/style | Edit `config.json` |
| Renew Instagram token | See [[Projects/Instagram Automation/Token renewal (every 60 days)|Token Renewal]] |

---

## Cloud backup

This vault syncs to **GitHub** automatically (code + Downloads/).
`Journal/` stays local only — put your Obsidian vault inside iCloud or OneDrive for phone access.
