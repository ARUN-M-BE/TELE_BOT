from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.membership_service import check_user_membership
import config
import database

router = Router()

@router.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    """Greets the user and checks membership immediately."""
    for user in message.new_chat_members:
        is_member = await check_user_membership(message.bot, user.id)
        
        status_text = "🟢 <b>Verified Member</b>" if is_member else "🔴 <b>Not Verified (Join Channel!)</b>"
        
        builder = InlineKeyboardBuilder()
        if not is_member:
            builder.button(text="📢 Join Channel", url=config.CHANNEL_URL)
            builder.button(text="✅ Verify Joining", callback_data="verify_join")
            builder.adjust(1)
            
        welcome_text = (
            f"👋 <b>Welcome to the Group, {user.full_name}!</b>\n\n"
            f"Status: {status_text}\n\n"
            "Please support our community by joining the channel below! 🚀"
        )
        
        await message.answer(welcome_text, reply_markup=builder.as_markup() if not is_member else None)
        
    # Optional: Delete the system join message
    try:
        await message.delete()
    except Exception:
        pass

@router.message(F.left_chat_member)
async def on_user_leave(message: types.Message):
    """Automatically deletes 'User Left' messages."""
    try:
        await message.delete()
    except Exception as e:
        print(f"JoinHider Error: {e}")

@router.message(Command("hi"))
async def say_hi(message: types.Message):
    """Simple greeting command."""
    await message.answer("👋 Hello! The <b>Hamster Super Bot</b> is active and working in this group! 🚀")

@router.message(Command("rules"))
async def show_rules(message: types.Message):
    """Displays group rules in the @FFR_Rules_787 friendly style."""
    rules_text = (
        "<b>✨ Hii Friends! Welcome to our Community! ✨</b>\n\n"
        "To keep our group safe and happy, please follow these rules: 🙏\n\n"
        "1. ❤️ <b>Be Respectful</b>: No bad language or fighting.\n"
        "2. 🚫 <b>No Spamming</b>: Don't send too many messages or stickers.\n"
        "3. 🔗 <b>No Links</b>: Don't share links to other channels or bots.\n"
        "4. 🛡 <b>Privacy First</b>: Never share your phone number or private info.\n"
        "5. 🐹 <b>Hamster Talk Only</b>: Keep the discussion related to the game!\n\n"
        "<i>Violating rules may result in a Mute or Ban. Let's grow together!</i> 🚀"
    )
    await message.answer(rules_text)

@router.message(Command("ban"))
async def ban_user(message: types.Message):
    """Simple ban command (Admin Only)."""
    # In a real scenario, check for admin perms
    if not message.reply_to_message:
        return await message.answer("Please reply to the user you want to ban.")
    
    try:
        await message.chat.ban(message.reply_to_message.from_user.id)
        await message.answer(f"✅ User <b>{message.reply_to_message.from_user.full_name}</b> has been banned.")
    except Exception as e:
        await message.answer(f"❌ Error: {e}")
