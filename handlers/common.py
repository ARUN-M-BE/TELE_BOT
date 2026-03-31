from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.membership_service import check_user_membership
import database

router = Router()

def get_search_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Daily Cipher", callback_data="search_cipher")
    builder.button(text="🧩 Daily Combo", callback_data="search_combo")
    builder.button(text="🎮 Mini Game", callback_data="search_minigame")
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(F.data == "verify_join")
async def verify_join_callback(callback: types.CallbackQuery):
    """Handles the 'Verify Joining' button across all handlers."""
    is_member = await check_user_membership(callback.bot, callback.from_user.id)
    if is_member:
        await callback.answer("✅ Success! You are now verified.")
        welcome_text = (
            f"👋 <b>Welcome back, {callback.from_user.full_name}!</b>\n\n"
            "🟢 <b>Status: Verified Member</b>\n"
            "Use the search buttons below to find Hamster Kombat updates:"
        )
        await callback.message.edit_text(welcome_text, reply_markup=get_search_keyboard())
    else:
        await callback.answer("❌ You haven't joined yet. Please join the channel first!", show_alert=True)
