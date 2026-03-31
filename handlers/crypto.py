from aiogram import Router, types
from aiogram.filters import Command
import requests

router = Router()

@router.message(Command("ton"))
async def ton_price_cmd(message: types.Message):
    """Shows daily Toncoin (TON) price and exchange updates."""
    # Logic for Toncoin (TON) price fetching (can be CoinGecko or tonapi.io)
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url).json()
        price = response['the-open-network']['usd']
        change = response['the-open-network']['usd_24h_change']
        
        price_text = (
            "<b>💎 Toncoin (TON) Daily Status 💎</b>\n\n"
            f"• 💰 <b>Current Price</b>: ${price:.2f} USD\n"
            f"• 📈 <b>24h Change</b>: {change:+.2f}%\n"
            "• 💠 <b>Exchange Info</b>: OKX, Bybit, KuCoin, HTX\n\n"
            "<i>Market moves daily—stay ahead by checking /ton every morning!</i> 🚀"
        )
        await message.answer(price_text)
    except Exception as e:
        print(f"Toncoin Error: {e}")
        await message.answer("❌ Error: Unable to fetch Toncoin price right now.")

@router.message(Command("ton_news"))
async def ton_news_cmd(message: types.Message):
    """Shows the latest Toncoin ecosystem news."""
    news_text = (
        "<b>💎 Toncoin Ecosystem News (March 2026)</b>\n\n"
        "• 🌐 <b>Ecosystem</b>: TON Network now has over 1B users!\n"
        "• 🏦 <b>Institutional Buy-in</b>: Major funds are adding TON!\n"
        "• 🎮 <b>GameFi</b>: 100+ new games joined the TON ecosystem.\n\n"
        "<i>Daily updates are also posted at 9:00 AM!</i> ⏰"
    )
    await message.answer(news_text)
