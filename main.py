import asyncio
import logging
import sys

# Force UTF-8 output on Windows to prevent emoji UnicodeEncodeError
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HamsterBot")

async def main():
    """Starts the Search Bot (aiogram only — no userbot/streamer)."""
    import bot  # Lazy import to avoid early event loop issues
    logger.info("[BOT] Starting Hamster Search Bot...")
    await bot.on_startup()
    logger.info("[BOT] Bot is live! Listening for messages...")
    await bot.dp.start_polling(bot.bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("[BOT] Shut down gracefully.")
