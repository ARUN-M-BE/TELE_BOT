from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

def get_search_keyboard():
    """Returns the quick-search inline keyboard for Hamster Kombat topics."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔐 Daily Cipher", callback_data="search_cipher")
    builder.button(text="🧩 Daily Combo",  callback_data="search_combo")
    builder.button(text="🎮 Mini Game",    callback_data="search_minigame")
    builder.adjust(1)
    return builder.as_markup()
