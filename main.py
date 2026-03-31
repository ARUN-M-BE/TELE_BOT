import asyncio
import bot
import streamer
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HamsterSuperBot")

async def main():
    """Starts both the Bot Client (aiogram) and the Streamer Client (pyrogram + pytgcalls) at once."""
    logger.info("🚀 Starting Unified Hamster Super Bot...")
    
    # Run bot and streamer in parallel
    try:
        # Start the Streamer (Userbot) first
        await streamer.init_streamer()
        
        # Then start the Bot's main loop
        await bot.dp.start_polling(bot.bot, on_startup=bot.on_startup)
        
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Shutting down Bot...")
        await streamer.userbot.stop()

if __name__ == "__main__":
    asyncio.run(main())
