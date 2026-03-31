from aiogram import Bot, Dispatcher, types
import config
import asyncio

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    print("📢 Log in to Telegram and Send any message to your channel AFTER adding this bot as ADMIN.")
    print("⏳ Waiting for updates... (Press Ctrl+C to stop)")
    
    offset = None
    while True:
        updates = await bot.get_updates(offset=offset, timeout=30)
        for update in updates:
            if update.message:
                print(f"✅ Group/User ID: {update.message.chat.id} (Name: {update.message.chat.full_name})")
            elif update.channel_post:
                print(f"✅ Channel ID: {update.channel_post.chat.id} (Name: {update.channel_post.chat.title})")
            elif update.my_chat_member:
                print(f"✅ New Chat ID: {update.my_chat_member.chat.id} (Name: {update.my_chat_member.chat.title})")
            
            offset = update.update_id + 1
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
