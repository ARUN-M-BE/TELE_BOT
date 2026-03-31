import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
import config
import database
from services import news_service
from handlers import group, hamster, crypto, multimedia, search

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bot
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Register Handlers
dp.include_router(group.router)
dp.include_router(hamster.router)
dp.include_router(crypto.router)
dp.include_router(multimedia.router)
dp.include_router(search.router)

async def on_startup():
    """Logic to run when the bot starts."""
    logger.info("Initializing Database...")
    await database.init_db()
    
    # Setup Daily News Scheduler
    if config.CHANNEL_ID:
        logger.info("Setting up Daily News Scheduler (9:00 AM)...")
        news_service.setup_scheduler(bot, config.CHANNEL_ID)

async def main():
    """Main loop for the aiogram bot."""
    await on_startup()
    logger.info("Bot is now listening for commands...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
