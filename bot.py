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

async def check_membership(user_id: int):
    """Checks membership with database caching."""
    # 1. Check DB first
    cached_status = await database.get_user_status(user_id)
    if cached_status:
        return True
    
    # 2. Check API
    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        is_joined = member.status in ["member", "administrator", "creator"]
        if is_joined:
            await database.set_user_joined(user_id, True)
        return is_joined
    except Exception as e:
        logger.error(f"Error checking membership for {user_id}: {e}")
        return False

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
    """Professional start handler with rich formatting."""
    is_admin = message.from_user.id in config.ADMIN_IDS
    joined = await check_membership(message.from_user.id)
    
    if joined or is_admin:
        status_text = "<b>✅ Admin Access Granted!</b>" if is_admin else "<b>✅ Access Granted!</b>"
        await message.answer(
            f"{status_text}\n\n"
            "You have full access to all bot features. Send a query to search YouTube."
        )
    else:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="📢 Join Our Channel", url=config.CHANNEL_URL))
        builder.row(types.InlineKeyboardButton(text="✅ Click to Verify", callback_data="verify_join"))
        
        await message.answer(
            "<b>👋 Welcome to the YouTube Archiver!</b>\n\n"
            "To maintain our community, we require all users to join our channel first.\n\n"
            "<i>Please join and click the button below to unlock the bot:</i>",
            reply_markup=builder.as_markup()
        )

@dp.callback_query(F.data == "verify_join")
async def verify_join(callback: types.CallbackQuery):
    """Verified join callback with alert."""
    is_admin = callback.from_user.id in config.ADMIN_IDS
    joined = await check_membership(callback.from_user.id)
    
    if joined or is_admin:
        await callback.answer("✅ Verification Successful!", show_alert=True)
        await callback.message.edit_text(
            "<b>✅ Access Unlocked!</b>\n\n"
            "You can now search and archive YouTube videos. Simply send a search query."
        )
    else:
        await callback.answer("❌ Verification Failed!\n\nPlease join the channel first.", show_alert=True)

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
    await start_cmd(message)

@dp.message()
async def handle_all_messages(message: types.Message):
    """Advanced message handler with state and permissions check."""
    if not message.text:
        return

    # 1. Enforcement: Must be joined
    is_admin = message.from_user.id in config.ADMIN_IDS
    if not is_admin:
        joined = await check_membership(message.from_user.id)
        if not joined:
            return await start_cmd(message)
    
    # 2. Logic: Process Admin Search
    if is_admin:
        # Show "Typing" or "Searching" status
        status_msg = await message.answer("<i>🔍 Searching YouTube...</i>")
        
        query = message.text
        url, title = search_youtube(query)
        
        if not url:
            return await status_msg.edit_text("<b>❌ No results found.</b> Try a different query.")

        # Save to Google Sheets
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        sheets_saved = save_to_sheets(now, url, query, message.message_id)
        
        # Prepare result text
        result_text = (
            f"<b>📺 {title}</b>\n\n"
            f"🔗 <a href='{url}'>Watch Now</a>\n\n"
            f"📅 <i>Log Status: {'✅ Archived' if sheets_saved else '⚠️ Search only'}</i>\n"
            f"⏰ <i>Deleting original in 10 minutes...</i>"
        )
        
        await status_msg.edit_text(result_text, disable_web_page_preview=False)
        
        # Schedule persistent deletion
        await database.add_pending_deletion(message.chat.id, message.message_id, config.AUTO_DELETE_MINUTES)

async def setup_commands():
    """Sets the bot's command menu."""
    commands = [
        BotCommand(command="start", description="Start/Unlock the bot"),
        BotCommand(command="help", description="How to use"),
        BotCommand(command="verify", description="Check membership")
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
