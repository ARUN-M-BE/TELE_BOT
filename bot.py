import asyncio
import datetime
import logging
import config
import database
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import BotCommand
from services.youtube_service import search_youtube
from services.sheets_service import save_to_sheets

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- Helpers ---

def get_search_keyboard():
    """Builds the main search keyboard for verified users."""
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🐹 Daily Cipher", callback_data="search_cipher"))
    builder.row(types.InlineKeyboardButton(text="🐹 Daily Combo", callback_data="search_combo"))
    return builder.as_markup()

async def check_membership(user_id: int, username: str = "Unknown"):
    """Checks membership with database caching and updates username."""
    # 1. Check DB first
    db_data = await database.get_user_status(user_id)
    if db_data and db_data[0]:  # is_joined
        return True, db_data[1]  # Return joined status and last_search_time
    
    # 2. Check API
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        is_joined = member.status in ["member", "administrator", "creator"]
        if is_joined:
            await database.set_user_joined(user_id, username, True)
        return is_joined, None
    except Exception as e:
        logger.error(f"Error checking membership for {user_id}: {e}")
        return False, None

# --- Persistent Deletion Task ---

async def deletion_loop():
    """Background task that checks for and handles expired message deletions."""
    while True:
        try:
            expired = await database.get_expired_deletions()
            for db_id, chat_id, message_id in expired:
                try:
                    await bot.delete_message(chat_id, message_id)
                    logger.info(f"Deleted message {message_id} in chat {chat_id}")
                except Exception as e:
                    logger.warning(f"Could not delete message {message_id}: {e}")
                
                await database.remove_deletion(db_id)
        except Exception as e:
            logger.error(f"Error in deletion loop: {e}")
        
        await asyncio.sleep(60)  # Check every minute

# --- Handlers ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    """Start handler following the new verification scenario."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    is_admin = user_id in config.ADMIN_IDS
    joined, _ = await check_membership(user_id, username)
    
    if joined or is_admin:
        await message.answer(
            f"<b>👋 Welcome back, {username}!</b>\n\n"
            "You are verified. Use the search buttons below to find Hamster Kombat updates:",
            reply_markup=get_search_keyboard()
        )
    else:
        builder = InlineKeyboardBuilder()
        # User specified two channel links, using same for both as requested
        builder.row(types.InlineKeyboardButton(text="📢 Join Channel 1", url=config.CHANNEL_URL))
        builder.row(types.InlineKeyboardButton(text="📢 Join Channel 2", url=config.CHANNEL_URL))
        builder.row(types.InlineKeyboardButton(text="✅ Click to Verify", callback_data="verify_join"))
        
        await message.answer(
            "<b>👋 Welcome to the YouTube Archiver!</b>\n\n"
            "To use this bot, please join our channels and click verify below:\n\n"
            f"🔗 <a href='{config.CHANNEL_URL}'>Join Hamster Dev Bot</a>",
            reply_markup=builder.as_markup()
        )

@dp.callback_query(F.data == "verify_join")
async def verify_join(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.full_name
    is_admin = user_id in config.ADMIN_IDS
    joined, _ = await check_membership(user_id, username)
    
    if joined or is_admin:
        await callback.answer("✅ Verification Successful!", show_alert=True)
        await callback.message.edit_text(
            f"<b>✅ Welcome, {username}!</b>\n\n"
            "Access Unlocked. Use the search buttons below to find updates:",
            reply_markup=get_search_keyboard()
        )
    else:
        await callback.answer("❌ Verification Failed!\n\nPlease join both channels first.", show_alert=True)

@dp.message(Command("help"))
async def help_cmd(message: types.Message):
    """Help command with instructions."""
    is_admin = message.from_user.id in config.ADMIN_IDS
    admin_note = "\n\n⭐ <b>Admin Note:</b> You have full access and bypass all joins." if is_admin else ""
    
    await message.answer(
        "<b>🛠 How to use this Bot:</b>\n\n"
        "1. Join our required channel.\n"
        "2. If you are an <b>Admin</b>, send any text to search YouTube.\n"
        "3. The bot will return the best video match.\n"
        "4. The result is automatically logged to Google Sheets.\n"
        "5. Your original message will be deleted after 10 minutes." + admin_note
    )

@dp.message(Command("verify"))
async def verify_cmd(message: types.Message):
    """Manual verification command."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    is_admin = user_id in config.ADMIN_IDS
    joined, _ = await check_membership(user_id, username)
    
    if joined or is_admin:
        await message.answer(
            f"<b>✅ Verification Status: Verified</b>\n\n"
            f"Welcome, {username}! Use the buttons below to find updates.",
            reply_markup=get_search_keyboard()
        )
    else:
        await start_cmd(message)

@dp.message()
async def handle_all_messages(message: types.Message):
    """Catch-all for admin custom searches."""
    if not message.text:
        return

    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    is_admin = user_id in config.ADMIN_IDS
    
    if is_admin:
        await yt_search(message, message.text, username)
    else:
        # For non-admins, if they send text, guide them to buttons
        joined, _ = await check_membership(user_id, username)
        if not joined:
            return await start_cmd(message)
        
        await message.answer(
            "⚠️ <b>Custom search is restricted.</b>\n\n"
            "Please use the search buttons provided above.",
            reply_markup=get_search_keyboard()
        )



@dp.callback_query(F.data.startswith("search_"))
async def handle_search_callbacks(callback: types.CallbackQuery):
    """Handles specific search queries from buttons and enforces cooldown."""
    query_map = {
        "search_cipher": "Hamster Kombat Daily Cipher",
        "search_combo": "Hamster Kombat Daily Combo"
    }
    
    query = query_map.get(callback.data)
    if query:
        user_id = callback.from_user.id
        username = callback.from_user.username or "Unknown"
        is_admin = user_id in config.ADMIN_IDS
        joined, last_search = await check_membership(user_id, username)
        
        if joined or is_admin:
            # Cooldown check for button clicks
            if last_search and not is_admin:
                last_time = datetime.datetime.fromisoformat(last_search) if isinstance(last_search, str) else last_search
                elapsed = (datetime.datetime.now() - last_time).total_seconds()
                if elapsed < 600:
                    return await callback.answer("⏳ Cooldown active. Try again later.", show_alert=True)

            # Hide buttons immediately as requested
            await callback.message.edit_reply_markup(reply_markup=None)
            
            # Perform search
            await callback.answer(f"🔍 Searching for: {query}")
            await yt_search(callback.message, query, username)
            
            # Start cooldown
            await database.update_last_search_time(user_id)
        else:
            await callback.answer("❌ Please join our channel first!", show_alert=True)
            await start_cmd(callback.message)

async def yt_search(message: types.Message, query: str, username: str):
    """Core function to handle YouTube search, logging, and scheduled deletion."""
    # Show "Searching" status with content protection enabled
    status_msg = await message.answer("<i>🔍 Searching YouTube...</i>", protect_content=True)
    
    url, title = search_youtube(query)
    
    if not url:
        return await status_msg.edit_text("<b>❌ No results found.</b> Try a different query.")

    # Save to Google Sheets
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sheets_saved = save_to_sheets(now, url, query, username, message.message_id)
    
    # Always Log Locally
    await database.log_search(now, url, query, username, message.message_id)
    
    # Prepare result text
    status_icon = "✅" if sheets_saved else "💾"
    status_text = "Archived to Sheets" if sheets_saved else "Logged Locally (Auto-Fallback)"
    
    result_text = (
        f"<b>📺 {title}</b>\n\n"
        f"🔗 <a href='{url}'>Watch Now</a>\n\n"
        f"📅 <i>Log Status: {status_icon} {status_text}</i>\n"
        f"⏰ <i>Cleaning up chat history in 10 minutes...</i>"
    )
    
    await status_msg.edit_text(result_text, disable_web_page_preview=False)
    
    # Schedule persistent deletion for both messages
    await database.add_pending_deletion(message.chat.id, message.message_id, config.AUTO_DELETE_MINUTES)
    await database.add_pending_deletion(message.chat.id, status_msg.message_id, config.AUTO_DELETE_MINUTES)

async def setup_commands():
    """Sets the bot's command menu."""
    commands = [
        BotCommand(command="start", description="Start/Unlock the bot"),
        BotCommand(command="verify", description="Check membership status"),
        BotCommand(command="help", description="How to use instructions")
    ]
    await bot.set_my_commands(commands)

async def main():
    """Application entry point with background tasks."""
    logger.info("Initializing Database...")
    await database.init_db()
    
    logger.info("Setting up Bot Commands...")
    await setup_commands()
    
    # Start background deletion loop
    asyncio.create_task(deletion_loop())
    
    logger.info("Bot is now polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot Stopped.")
