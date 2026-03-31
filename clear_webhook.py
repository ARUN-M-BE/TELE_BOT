import asyncio
from aiogram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ No BOT_TOKEN found in .env")
        return

    bot = Bot(token=token)
    print(f"🔄 Clearing webhook for bot...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook cleared and pending updates dropped!")
    except Exception as e:
        print(f"❌ Error clearing webhook: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
