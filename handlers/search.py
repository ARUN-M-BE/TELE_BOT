"""
Clean YouTube Search Handler — no AI dependency.
Features:
- /start  → Welcome + membership check + quick search buttons
- /search  → Searches YouTube for the query, returns top result
- /today   → Shows today's cached daily update
- /ask     → Removed (was AI-only)
- Inline buttons → Cipher, Combo, Minigame instant YouTube search
"""

import asyncio
import datetime
import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from googleapiclient.discovery import build

import config
import database
import services.sheets_service as sheets
from handlers.common import get_search_keyboard
from services.membership_service import check_user_membership

logger = logging.getLogger("SearchHandler")
router = Router()


# ─── YouTube Search ───────────────────────────────────────────────────────────

async def _yt_search(query: str) -> tuple:
    """Finds the most recent YouTube video for the query. Returns (title, url)."""
    try:
        def _sync():
            yt = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
            req = yt.search().list(
                q=query,
                part="snippet",
                maxResults=1,
                type="video",
                order="date"
            )
            res = req.execute()
            if res.get("items"):
                item = res["items"][0]
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                channel = item["snippet"]["channelTitle"]
                thumb = item["snippet"]["thumbnails"]["high"]["url"]
                published = item["snippet"]["publishedAt"][:10]
                url = f"https://www.youtube.com/watch?v={video_id}"
                return title, url, channel, published
            return None, None, None, None

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync)
    except Exception as e:
        logger.error(f"YouTube search error: {e}")
        return None, None, None, None


def _format_result(label: str, query: str, title: str, url: str, channel: str, published: str) -> str:
    """Formats a YouTube search result as a clean Telegram HTML message."""
    return (
        f"🔍 <b>{label}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎬 <b>{title}</b>\n\n"
        f"📺 <i>Channel:</i> {channel}\n"
        f"📅 <i>Published:</i> {published}\n\n"
        f"🔗 {url}\n\n"
        f"<i>🔎 Search: {query}</i>"
    )


async def _log(user, query: str, url: str, msg_id: int):
    username = user.username or user.full_name or "Unknown"
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await database.log_search(date_str, url, query, username, msg_id)
    await sheets.save_to_sheets(date_str, url, query, username, msg_id)


# ─── /start ───────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    is_member = await check_user_membership(message.bot, user_id)

    if is_member:
        await database.set_user_joined(user_id, username, True)
        await message.answer(
            f"👋 <b>Welcome, {message.from_user.full_name}!</b>\n\n"
            "🟢 <b>Status: Verified Member ✅</b>\n\n"
            "🐹 <b>Hamster Kombat Search Bot</b>\n"
            "Use the buttons below to instantly find today's:\n\n"
            "🔐 Daily Cipher\n"
            "🧩 Daily Combo\n"
            "🎮 Mini Game Solution\n\n"
            "Or use: <code>/search your topic</code>",
            reply_markup=get_search_keyboard()
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Join Our Channel", url=config.CHANNEL_URL)
        builder.button(text="✅ I've Joined — Verify Me", callback_data="verify_join")
        builder.adjust(1)
        await message.answer(
            f"🔒 <b>Access Restricted!</b>\n\n"
            f"Hi <b>{message.from_user.full_name}</b>! 👋\n\n"
            "Please join our channel first, then click <b>Verify Me</b>.",
            reply_markup=builder.as_markup()
        )


# ─── /search ─────────────────────────────────────────────────────────────────

@router.message(Command("search"))
async def search_handler(message: types.Message):
    """/search <query> — Searches YouTube and returns the top result."""
    is_member = await check_user_membership(message.bot, message.from_user.id)
    if not is_member:
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Join Channel", url=config.CHANNEL_URL)
        return await message.answer(
            "🔒 <b>Members only!</b> Join the channel first.",
            reply_markup=builder.as_markup()
        )

    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        return await message.answer(
            "🔍 <b>Usage:</b> <code>/search your topic</code>\n\n"
            "Example: <code>/search Hamster Kombat cipher today</code>"
        )

    query = args[1].strip()
    thinking = await message.answer(f"🔍 <i>Searching YouTube for:</i> <b>{query[:60]}</b>...")

    title, url, channel, published = await _yt_search(query)
    if title and url:
        text = _format_result("YouTube Search Result", query, title, url, channel, published)
        await thinking.edit_text(text, disable_web_page_preview=False)
        await _log(message.from_user, query, url, thinking.message_id)
    else:
        await thinking.edit_text(
            f"❌ <b>No results found</b> for: <i>{query}</i>\n\n"
            "Try a more specific search term."
        )

    await database.add_pending_deletion(thinking.chat.id, thinking.message_id, config.AUTO_DELETE_MINUTES)


# ─── /today ──────────────────────────────────────────────────────────────────

@router.message(Command("today"))
async def today_handler(message: types.Message):
    """/today — Shows the cached daily update or searches for it live."""
    is_member = await check_user_membership(message.bot, message.from_user.id)
    if not is_member:
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Join Channel", url=config.CHANNEL_URL)
        return await message.answer(
            "🔒 <b>Members only!</b> Join the channel first.",
            reply_markup=builder.as_markup()
        )

    cached = await database.get_hamster_news()
    if cached:
        await message.answer(
            f"📅 <b>Today's Cached Update:</b>\n\n{cached}",
            reply_markup=get_search_keyboard()
        )
    else:
        thinking = await message.answer("🔍 <i>Fetching today's update...</i>")
        query = "Hamster Kombat Daily Update Today"
        title, url, channel, published = await _yt_search(query)
        if title and url:
            post = _format_result("Today's Hamster Kombat Update", query, title, url, channel, published)
            await thinking.edit_text(post, disable_web_page_preview=False)
            await database.update_hamster_news(post)
        else:
            await thinking.edit_text(
                "⚠️ <b>No update available yet.</b>\n\n"
                "The daily post appears here after 9:00 AM ⏰\n"
                "Or use the buttons below to search manually!",
                reply_markup=get_search_keyboard()
            )


# ─── Inline Button Callbacks ──────────────────────────────────────────────────

SEARCH_TOPICS = {
    "search_cipher": ("Hamster Kombat Daily Cipher Today", "🔐 Daily Cipher"),
    "search_combo": ("Hamster Kombat Daily Combo Today", "🧩 Daily Combo"),
    "search_minigame": ("Hamster Kombat Mini Game Solution Today", "🎮 Mini Game"),
}


@router.callback_query(F.data.startswith("search_"))
async def handle_search_callbacks(callback: types.CallbackQuery):
    action = callback.data
    if action not in SEARCH_TOPICS:
        return await callback.answer("Unknown action.")

    query, label = SEARCH_TOPICS[action]
    await callback.answer(f"🔍 Searching {label}...")

    is_member = await check_user_membership(callback.bot, callback.from_user.id)
    if not is_member:
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Join Channel", url=config.CHANNEL_URL)
        return await callback.message.answer(
            "🔒 <b>Members only!</b> Join the channel first.",
            reply_markup=builder.as_markup()
        )

    thinking = await callback.message.answer(
        f"🔍 <i>Searching YouTube for <b>{label}</b>...</i>"
    )

    title, url, channel, published = await _yt_search(query)
    if title and url:
        text = _format_result(label, query, title, url, channel, published)
        await thinking.edit_text(text, disable_web_page_preview=False)
        await _log(callback.from_user, query, url, thinking.message_id)
    else:
        await thinking.edit_text(
            f"❌ <b>No result found for {label}</b>\n\nTry again shortly!"
        )

    await database.add_pending_deletion(thinking.chat.id, thinking.message_id, config.AUTO_DELETE_MINUTES)
