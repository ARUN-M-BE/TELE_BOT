# No top-level imports of bot or streamer to avoid early event loop initialization issues with Pyrogram
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HamsterSuperBot")

async def main():
    """Starts both the Bot Client (aiogram) and the Streamer Client (pyrogram + pytgcalls) together."""
    import bot # Lazy import
    import streamer # Lazy import
    from streamer import Streamer # Lazy import

    logger.info("🚀 Starting Unified Hamster Super Bot...")
    
    streamer_instance = Streamer()

    # We run both in parallel using gather to ensure they share the same event loop
    logger.info("Connecting to Telegram Services...")
    
    await asyncio.gather(
        bot.on_startup(), # Initialize DB and Webhook cleanup
        streamer_instance.start(), # Start Userbot in background
        bot.dp.start_polling(bot.bot) # Start main polling
    )

if __name__ == "__main__":
    import asyncio
    try:
        # Use run() for the entry point
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Shutting down Bot...")

if __name__ == "__main__":
    asyncio.run(main())
