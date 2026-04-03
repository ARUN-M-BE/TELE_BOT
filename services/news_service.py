"""
Daily Auto-Post Service — posts Hamster Kombat updates at 6:00 PM every day.
Uses YouTube API to find the latest cipher/combo/minigame videos.
No AI dependency — clean, reliable, formatted posts.
"""
import asyncio
import logging
import datetime
import requests

import config
import database
from googleapiclient.discovery import build
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("NewsService")

DAILY_TOPICS = [
    ("Hamster Kombat Daily Cipher Today",        "🔐 Daily Cipher"),
    ("Hamster Kombat Daily Combo Today",          "🧩 Daily Combo"),
    ("Hamster Kombat Mini Game Solution Today",   "🎮 Mini Game Solution"),
]


def _yt_top(query: str):
    """Returns (title, url) of the most recent YouTube video for query."""
    try:
        yt = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
        res = yt.search().list(
            q=query, part="snippet", maxResults=1, type="video", order="date"
        ).execute()
        if res.get("items"):
            item = res["items"][0]
            vid_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            published = item["snippet"]["publishedAt"][:10]
            return title, f"https://www.youtube.com/watch?v={vid_id}", channel, published
    except Exception as e:
        logger.error(f"YouTube error for '{query}': {e}")
    return None, None, None, None


def _ton_price() -> float:
    try:
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd",
            timeout=8
        ).json()
        return r["the-open-network"]["usd"]
    except Exception:
        return 0.0


def _build_post(label: str, query: str, title: str, url: str, channel: str, published: str) -> str:
    return (
        f"<b>{label}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎬 <b>{title}</b>\n\n"
        f"📺 <i>{channel}</i>  •  📅 <i>{published}</i>\n\n"
        f"🔗 {url}"
    )


async def post_daily_update(bot, chat_id):
    """Posts cipher + combo + minigame videos + TON price to the channel."""
    logger.info(f"📤 Daily auto-post to {chat_id}...")
    today = datetime.date.today().strftime("%A, %B %d, %Y")
    ton = _ton_price()

    await bot.send_message(
        chat_id,
        f"🌅 <b>Good Morning, Hamsters!</b> 🐹\n\n"
        f"📅 <b>{today}</b>\n"
        f"💎 <b>TON Price:</b> <i>${ton:.2f} USD</i>\n\n"
        f"Here are today's solutions! 👇"
    )

    loop = asyncio.get_event_loop()
    for query, label in DAILY_TOPICS:
        try:
            title, url, channel, published = await loop.run_in_executor(None, _yt_top, query)
            if title and url:
                post = _build_post(label, query, title, url, channel, published)
                sent = await bot.send_message(chat_id, post, disable_web_page_preview=False)
                await database.update_hamster_news(post)
            else:
                await bot.send_message(chat_id, f"⚠️ <b>{label}:</b> No video found today.")
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Failed to post {label}: {e}")

    await bot.send_message(
        chat_id,
        "✅ <b>Daily update done!</b>\n\n"
        "🔔 See you tomorrow at <b>6:00 PM</b>! ⏰\n"
        "💬 Use /search to find anything anytime."
    )
    logger.info("✅ Daily posts sent.")


def setup_scheduler(bot, chat_id):
    """Schedules daily post at 6:00 PM server time."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        post_daily_update,
        trigger="cron",
        hour=18,
        minute=0,
        args=(bot, chat_id),
        id="daily_hamster_post",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"🕘 Daily auto-post scheduled at 6:00 PM → chat {chat_id}")
    return scheduler
