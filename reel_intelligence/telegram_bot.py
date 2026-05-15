"""
Alvvo Brain Bot — Telegram → reel_ingest pipeline.

Flow:
  user pastes IG link  ->  bot asks "Art or Edu?"  ->  user taps button
  ->  bot runs reel_ingest in a thread  ->  replies with summary + vault path

Run:
  python telegram_bot.py
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import reel_ingest

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger("alvvo-bot")

URL_RE = re.compile(r"https?://\S+")
ALLOWED_USER = os.environ.get("TELEGRAM_ALLOWED_USER_ID", "").strip()

WELCOME = (
    "Alvvo Brain online.\n"
    "Send any IG / TikTok / YouTube reel link.\n"
    "I'll ask which bucket — Art or Edu — then file it to your vault."
)


def _gate(update: Update) -> bool:
    if not ALLOWED_USER:
        return True
    return str(update.effective_user.id) == ALLOWED_USER


async def start(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _gate(update):
        return
    await update.message.reply_text(WELCOME + f"\n\nyour user id: {update.effective_user.id}")


async def on_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _gate(update):
        return
    text = update.message.text or ""
    m = URL_RE.search(text)
    if not m:
        await update.message.reply_text("Send a link.")
        return
    url = m.group(0)
    key = str(abs(hash(url)))[:10]
    ctx.bot_data.setdefault("pending", {})[key] = url
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("Art", callback_data=f"art|{key}"),
        InlineKeyboardButton("Edu", callback_data=f"edu|{key}"),
    ]])
    await update.message.reply_text(f"Bucket?\n{url}", reply_markup=kb)


async def on_pick(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    if not _gate(update):
        return
    bucket, key = q.data.split("|", 1)
    url = ctx.bot_data.get("pending", {}).pop(key, None)
    if not url:
        await q.edit_message_text("Link expired — send it again.")
        return
    await q.edit_message_text(f"Ingesting → {bucket}\n{url}\n\n(this takes ~30-90s)")

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(None, reel_ingest.ingest, url, bucket, False)
    except Exception as e:
        log.exception("ingest failed")
        await q.message.reply_text(f"Failed: {e}")
        return

    synth = result.get("synth") or {}
    info = result.get("info") or {}
    note_path = result.get("note_path")
    summary_lines = [
        f"Filed → {bucket}",
        f"@{info.get('uploader_id') or info.get('uploader') or 'unknown'}",
        f"Score: {synth.get('score', '?')}/10",
        f"{synth.get('one_line_summary', '')}",
        "",
        f"Hook: {synth.get('hook', '')[:200]}",
        f"Steal: {synth.get('steal_worthy', '')[:200]}",
        "",
        f"Path: {note_path}",
    ]
    await q.message.reply_text("\n".join(s for s in summary_lines if s is not None))


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing in .env")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_pick))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_link))
    log.info("alvvo brain bot up — long polling")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
