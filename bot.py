import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
import config
import database
from services import news_service
from handlers import group, hamster, crypto, search, common

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bot
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Register Handlers — order matters!
# Specific command routers first, then group catch-all guard last
dp.include_router(common.router)   # verify_join callback + search keyboard
dp.include_router(search.router)   # /start, /search, /today, search_* callbacks
dp.include_router(hamster.router)  # /season2, /hamster_news
dp.include_router(group.router)    # join verification, message guard, admin cmds

# Debug Middleware
@dp.message.outer_middleware()
async def logger_middleware(handler, event, data):
    if event.chat.type in ["group", "supergroup"]:
        print(f"📩 [Group Debug] {event.from_user.full_name}: {event.text or '[Media]'}")
    return await handler(event, data)

async def send_startup_test_message(bot, chat_id):
    """Sends a test message to the channel and deletes it after 2 minutes."""
    try:
        msg = await bot.send_message(
            chat_id,
            "🤖 <b>Bot controls are ACTIVE.</b> All systems operational! ✅\n"
            "<i>This test message will auto-delete in 2 minutes...</i>"
        )
        await asyncio.sleep(120)  # Wait 2 minutes
        await msg.delete()
    except Exception as e:
        logger.warning(f"Failed to send startup test message: {e}")

async def on_startup():
    """Logic to run when the bot starts."""
    logger.info("Initializing Database...")
    await database.init_db()

    logger.info("Clearing Webhook and Dropping Pending Updates...")
    await bot.delete_webhook(drop_pending_updates=True)

    if config.CHANNEL_ID:
        # Send startup test message in background
        logger.info("Sending startup test message to channel...")
        asyncio.create_task(send_startup_test_message(bot, config.CHANNEL_ID))

        # Setup Daily News Scheduler at 6:00 PM
        logger.info("Setting up Daily News Scheduler (6:00 PM)...")
        news_service.setup_scheduler(bot, config.CHANNEL_ID)

async def main():
    """Main loop for the aiogram bot."""
    await on_startup()
    logger.info("🤖 AI Search Bot is now live and listening...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
