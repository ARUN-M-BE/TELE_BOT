from aiogram import Router, types
from aiogram.filters import Command
import datetime

router = Router()

@router.message(Command("season2"))
async def hamster_season2(message: types.Message):
    """Shows Hamster Kombat Season 2 status and Season 1 review."""
    review_text = (
        "<b>🐹 Hamster Kombat: The Journey 🐹</b>\n\n"
        "<b>📦 Season 1: The CEO Era (Review)</b>\n"
        "• <b>Airdrop</b>: Sept 26, 2024\n"
        "• <b>Supply</b>: 100 Billion $HMSTR\n"
        "• <b>Method</b>: Tap-to-Earn & PPH (Profit Per Hour)\n"
        "• <b>Status</b>: ✅ Completed & Listed Everywhere!\n\n"
        "<b>🚀 Season 2: The HamsterVerse (Interlude)</b>\n"
        "• <b>Status</b>: 🎮 In Progress - <b>Game Studio CEO Mode</b>\n"
        "• <b>Theme</b>: Build games, manage staff, hire devs!\n"
        "• <b>Expected Airdrop</b>: Summer 2025/2026 (Dates TBD)\n"
        "• <b>Method</b>: Proof of Engagement (PoE) & NFT items\n\n"
        "<b>🔥 Daily News & Updates:</b>\n"
        "Check /hamster_news for more detailed game studio tips!"
    )
    await message.answer(review_text)

@router.message(Command("hamster_news"))
async def hamster_news_cmd(message: types.Message):
    """Shows the latest Hamster Kombat news."""
    # This could be fetched from database or recent scraping
    news_text = (
        "<b>📣 Latest Hamster Kombat News (March 2026)</b>\n\n"
        "• 🧩 <b>NFT Marketplace</b>: Launched for internal items!\n"
        "• 💰 <b>Staking 2.0</b>: Staking $HMSTR now earns you dev points.\n"
        "• 📉 <b>Price Check</b>: $HMSTR trading at ~0.00015 USDT.\n\n"
        "<i>Stay tuned for daily updates at 9:00 AM!</i> ⏰"
    )
    await message.answer(news_text)
