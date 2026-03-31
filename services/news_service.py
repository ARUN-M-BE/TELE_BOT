import asyncio
import database
import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def fetch_latest_news():
    """Fetches the latest news for Hamster Kombat and Toncoin."""
    # Simulation: In a real scenario, this would scrape a news channel or use an API
    news = (
        "<b>🐹 Hamster Kombat Daily Update (March 2026)</b>\n\n"
        "• 🧩 <b>HamsterVerse</b>: A new staff member 'Super Dev' is now available!\n"
        "• 💰 <b>Staking</b>: APR for $HMSTR increased to 12%.\n"
        "• 🚀 <b>Token Exchange</b>: Expected summer 2026 update soon.\n"
        "• 💎 <b>Toncoin (TON)</b>: Current price at ${price:.2f} USD.\n\n"
        "<i>Stay tuned for more updates tomorrow at 9:00 AM!</i> ⏰"
    )
    
    # Get current TON price for the news
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd"
        response = requests.get(url).json()
        price = response['the-open-network']['usd']
    except:
        price = 0
        
    return news.format(price=price)

async def post_daily_news(bot, chat_id):
    """Automatically posts the daily news to the specified group."""
    news = await fetch_latest_news()
    await bot.send_message(chat_id, news)
    # Cache news in DB
    await database.update_hamster_news(news)

def setup_scheduler(bot, chat_id):
    """Sets up the 9 AM daily news auto-post scheduler."""
    scheduler = AsyncIOScheduler()
    # Posts every day at 9:00 AM local server time
    scheduler.add_job(post_daily_news, 'cron', hour=9, minute=0, args=(bot, chat_id))
    scheduler.start()
    return scheduler
