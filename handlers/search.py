from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.membership_service import check_user_membership
from handlers.common import get_search_keyboard
import services.sheets_service as sheets
from googleapiclient.discovery import build
import datetime
import config
import database

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    """Greets the user and shows search buttons if verified."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    
    # Check real membership
    is_member = await check_user_membership(message.bot, user_id)
    
    if is_member:
        await database.set_user_joined(user_id, username, True)
        welcome_text = (
            f"👋 <b>Welcome back, {message.from_user.full_name}!</b>\n\n"
            "🟢 <b>Status: Verified Member</b>\n"
            "Use the search buttons below to find Hamster Kombat updates:"
        )
        await message.answer(welcome_text, reply_markup=get_search_keyboard())
    else:
        # Show join link if not a member
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Join Our Channel", url=config.CHANNEL_URL)
        builder.button(text="✅ Verify Joining", callback_data="verify_join")
        builder.adjust(1)
        
        await message.answer(
            f"📥 <b>Access Restricted!</b>\n\nHi {message.from_user.full_name}, "
            "Please join our channel first to use this bot's search features.",
            reply_markup=builder.as_markup()
        )

async def perform_yt_search(query: str):
    """Searches YouTube using the API."""
    try:
        youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
        request = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=1,
            type="video"
        )
        response = request.execute()
        if response['items']:
            video = response['items'][0]
            title = video['snippet']['title']
            video_id = video['id']['videoId']
            return f"<b>{title}</b>\nhttps://www.youtube.com/watch?v={video_id}"
        return "No results found."
    except Exception as e:
        print(f"YT Search Error: {e}")
        return "Error performing search."

@router.callback_query(F.data.startswith("search_"))
async def handle_search_callbacks(callback: types.CallbackQuery):
    """Handles search button clicks."""
    query_map = {
        "search_cipher": "Hamster Kombat Daily Cipher Today",
        "search_combo": "Hamster Kombat Daily Combo Today",
        "search_minigame": "Hamster Kombat Mini Game Solution Today"
    }
    
    action = callback.data
    query = query_map.get(action)
    
    if not query:
        return
        
    await callback.answer("Searching YouTube... 🔍")
    result = await perform_yt_search(query)
    
    # Send result and set for auto-deletion
    msg = await callback.message.answer(result)
    await database.add_pending_deletion(msg.chat.id, msg.message_id, config.AUTO_DELETE_MINUTES)
    
    # Log to Sheets and DB
    username = callback.from_user.username or callback.from_user.full_name
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Find URL in result
    url = result.split("\n")[-1] if "http" in result else "N/A"
    
    await database.log_search(date_str, url, query, username, msg.message_id)
    await sheets.save_to_sheets(date_str, url, query, username)
