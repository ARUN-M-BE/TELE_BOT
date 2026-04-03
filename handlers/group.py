"""
Full Group Control Handler
- Auto-join verification with 5-second countdown + auto-kick if not member
- Message management: anti-link, anti-spam, flood control, anti-forward
- Admin commands: /ban, /unban, /mute, /unmute, /kick, /warn, /purge, /lock, /unlock
- Welcome/leave message handling
"""

import asyncio
import re
import logging
import datetime
from collections import defaultdict

from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ChatPermissions

from services.membership_service import check_user_membership
import config

logger = logging.getLogger("GroupControl")
router = Router()

# ─── Constants ────────────────────────────────────────────────────────────────
JOIN_CHECK_DELAY = 5          # seconds before auto-checking membership
FLOOD_LIMIT = 5               # messages
FLOOD_WINDOW = 6              # seconds
MAX_WARNS = 3                 # warns before auto-ban

# URL pattern to detect links (except youtube & t.me/channel)
LINK_PATTERN = re.compile(
    r"(https?://|www\.|t\.me/\+|t\.me/joinchat|bit\.ly|tinyurl\.com)",
    re.IGNORECASE
)

# ─── In-memory state ──────────────────────────────────────────────────────────
# flood_tracker[chat_id][user_id] = list of message timestamps
flood_tracker: dict = defaultdict(lambda: defaultdict(list))
# pending_verification[user_id] = True (being verified)
pending_verification: set = set()
# warn_count[chat_id][user_id] = int
warn_count: dict = defaultdict(lambda: defaultdict(int))
# locked chats
locked_chats: set = set()

# ─── Helper: Is admin? ────────────────────────────────────────────────────────
async def _is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    if user_id in config.ADMIN_IDS:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

# ─── Helper: Mute/Unmute user ─────────────────────────────────────────────────
async def _mute_user(bot: Bot, chat_id: int, user_id: int):
    """Restricts all permissions for a user."""
    try:
        await bot.restrict_chat_member(
            chat_id, user_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
        )
    except Exception as e:
        logger.warning(f"Mute failed for {user_id}: {e}")

async def _unmute_user(bot: Bot, chat_id: int, user_id: int):
    """Restores all default permissions for a user."""
    try:
        await bot.restrict_chat_member(
            chat_id, user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
                can_change_info=False
            )
        )
    except Exception as e:
        logger.warning(f"Unmute failed for {user_id}: {e}")

# ─── NEW USER JOIN — 5-Second Auto-Verification ───────────────────────────────
@router.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    """
    When a user joins:
    1. Delete the system join message
    2. Mute them immediately
    3. Send a countdown welcome with Join button
    4. After 5 seconds, auto-check membership
       → If member: unmute + welcome message
       → If not: kick + notify
    """
    # Delete system "X joined" message
    try:
        await message.delete()
    except Exception:
        pass

    for user in message.new_chat_members:
        if user.is_bot:
            continue  # Skip bots

        user_id = user.id
        chat_id = message.chat.id
        bot = message.bot

        # Skip admins — no restriction
        if await _is_admin(bot, chat_id, user_id):
            await message.answer(
                f"👑 <b>Welcome, Admin {user.full_name}!</b>\n"
                f"You have full access to this group. 🚀"
            )
            continue

        # Check if they are already in the channel!
        is_member = await check_user_membership(bot, user_id)
        if is_member:
            await _unmute_user(bot, chat_id, user_id)
            await message.answer(
                f"✅ <b>Welcome, {user.full_name}!</b>\n\n"
                f"🟢 <b>Verified Member — Access Unlocked!</b>\n\n"
                f"🐹 You can now chat freely in the group.\n"
                f"Use /start to explore features. 🚀"
            )
            continue

        # Not a member — Mute them for 5s and ask to join
        await _mute_user(bot, chat_id, user_id)
        pending_verification.add(user_id)

        # 2) Send countdown welcome message
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Join Channel Now", url=config.CHANNEL_URL)
        builder.adjust(1)

        welcome_msg = await message.answer(
            f"👋 <b>Welcome, {user.full_name}!</b>\n\n"
            f"🔒 <b>You are muted for 5 seconds.</b>\n\n"
            f"📋 To <b>unlock</b> your access:\n"
            f"1️⃣ Join our channel (button below)\n"
            f"2️⃣ Your membership will be <b>verified automatically</b>!\n\n"
            f"⏳ <b>Auto-checking in 5 seconds...</b>",
            reply_markup=builder.as_markup()
        )

        # 3) Schedule auto-check after 5 seconds (non-blocking)
        asyncio.create_task(
            _auto_verify(bot, chat_id, user_id, user.full_name, welcome_msg)
        )


async def _auto_verify(bot: Bot, chat_id: int, user_id: int, full_name: str, welcome_msg: types.Message):
    """Runs after JOIN_CHECK_DELAY seconds and verifies membership."""
    await asyncio.sleep(JOIN_CHECK_DELAY)

    try:
        is_member = await check_user_membership(bot, user_id)

        if is_member:
            # ✅ Verified — unmute and welcome properly
            await _unmute_user(bot, chat_id, user_id)
            pending_verification.discard(user_id)

            try:
                await welcome_msg.edit_text(
                    f"✅ <b>Welcome, {full_name}!</b>\n\n"
                    f"🟢 <b>Verified Member — Access Unlocked!</b>\n\n"
                    f"🐹 You can now chat freely in the group.\n"
                    f"Use /start to explore features. 🚀"
                )
            except Exception:
                await bot.send_message(
                    chat_id,
                    f"✅ <b>{full_name}</b> has been verified and can now chat! 🟢"
                )
        else:
            # ❌ Not a member — kick them
            pending_verification.discard(user_id)
            try:
                await welcome_msg.edit_text(
                    f"❌ <b>{full_name}</b> was not verified.\n"
                    f"<i>Join the channel to re-enter the group.</i>"
                )
            except Exception:
                pass

            await asyncio.sleep(1)
            try:
                await bot.ban_chat_member(chat_id, user_id)
                await asyncio.sleep(1)
                # Unban so they can rejoin after joining the channel
                await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
            except Exception as e:
                logger.warning(f"Kick failed for {user_id}: {e}")

    except Exception as e:
        logger.error(f"Auto-verify error for {user_id}: {e}")


# ─── USER LEAVE ───────────────────────────────────────────────────────────────
@router.message(F.left_chat_member)
async def on_user_leave(message: types.Message):
    """Silently deletes 'X left the group' system messages."""
    try:
        await message.delete()
    except Exception:
        pass


# ─── VERIFY BUTTON (manual) ──────────────────────────────────────────────────
@router.callback_query(F.data == "verify_join")
async def manual_verify(callback: types.CallbackQuery):
    """Handles the manual 'I've Joined — Verify Me' button click."""
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id
    bot = callback.bot

    is_member = await check_user_membership(bot, user_id)
    if is_member:
        await _unmute_user(bot, chat_id, user_id)
        pending_verification.discard(user_id)
        await callback.answer("✅ Verified! You can now chat.", show_alert=True)
        try:
            await callback.message.edit_text(
                f"✅ <b>Welcome, {callback.from_user.full_name}!</b>\n"
                f"🟢 <b>Access Unlocked!</b> You can now chat freely. 🚀"
            )
        except Exception:
            pass
    else:
        await callback.answer(
            "❌ You haven't joined the channel yet!\nJoin and try again.",
            show_alert=True
        )


# ─── MESSAGE GUARD MIDDLEWARE ─────────────────────────────────────────────────
@router.message(F.chat.type.in_({"group", "supergroup"}))
async def group_message_guard(message: types.Message):
    """
    Monitors ALL group messages for:
    - Links (non-admins)
    - Sticker/GIF/animation spam
    - Forwarded channel messages
    - Flood control (5 msgs / 6 sec)
    - Locked group
    """
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    bot = message.bot

    # Bot's own messages — ignore
    if user_id == (await bot.get_me()).id:
        return

    is_admin = await _is_admin(bot, chat_id, user_id)

    # ── 1. Group Lock ──────────────────────────────────────────────────────
    if chat_id in locked_chats and not is_admin:
        try:
            await message.delete()
        except Exception:
            pass
        return

    # ── 2. Anti-Link ──────────────────────────────────────────────────────
    if not is_admin and message.text and LINK_PATTERN.search(message.text):
        try:
            await message.delete()
        except Exception:
            pass
        warn_count[chat_id][user_id] += 1
        warns = warn_count[chat_id][user_id]
        if warns >= MAX_WARNS:
            try:
                await bot.ban_chat_member(chat_id, user_id)
                await bot.send_message(
                    chat_id,
                    f"🚫 <b>{message.from_user.full_name}</b> was <b>banned</b> after {MAX_WARNS} warnings. (Link spam)"
                )
                warn_count[chat_id][user_id] = 0
            except Exception as e:
                logger.warning(f"Ban error: {e}")
        else:
            warning_msg = await message.answer(
                f"⚠️ <b>{message.from_user.full_name}</b>, links are not allowed!\n"
                f"<i>Warning {warns}/{MAX_WARNS}</i>"
            )
            await asyncio.sleep(5)
            try:
                await warning_msg.delete()
            except Exception:
                pass
        return

    # ── 3. Anti-Sticker/GIF spam (non-members only) ───────────────────────
    if not is_admin and (message.sticker or message.animation or message.video_note):
        is_member = await check_user_membership(bot, user_id)
        if not is_member:
            try:
                await message.delete()
            except Exception:
                pass
            return

    # ── 4. Anti-Forward from channels ─────────────────────────────────────
    if not is_admin and message.forward_from_chat:
        try:
            await message.delete()
        except Exception:
            pass
        fwd_warn = await message.answer(
            f"🚫 <b>{message.from_user.full_name}</b>, forwarding from channels is not allowed!"
        )
        await asyncio.sleep(5)
        try:
            await fwd_warn.delete()
        except Exception:
            pass
        return

    # ── 5. Flood Control ──────────────────────────────────────────────────
    if not is_admin:
        now = datetime.datetime.now().timestamp()
        user_times = flood_tracker[chat_id][user_id]
        # Remove old timestamps outside the window
        user_times[:] = [t for t in user_times if now - t < FLOOD_WINDOW]
        user_times.append(now)

        if len(user_times) >= FLOOD_LIMIT:
            try:
                await message.delete()
            except Exception:
                pass
            # Mute for 60 seconds
            try:
                until = datetime.datetime.now() + datetime.timedelta(seconds=60)
                await bot.restrict_chat_member(
                    chat_id, user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until
                )
                flood_warn = await bot.send_message(
                    chat_id,
                    f"🌊 <b>{message.from_user.full_name}</b> is sending too fast!\n"
                    f"<i>Muted for 60 seconds.</i>"
                )
                await asyncio.sleep(6)
                try:
                    await flood_warn.delete()
                except Exception:
                    pass
                flood_tracker[chat_id][user_id] = []
            except Exception as e:
                logger.warning(f"Flood mute error: {e}")
            return


# ─── ADMIN COMMANDS ───────────────────────────────────────────────────────────

async def _require_admin(message: types.Message) -> bool:
    """Returns True if sender is admin, else sends error."""
    if await _is_admin(message.bot, message.chat.id, message.from_user.id):
        return True
    await message.answer("❌ <b>Admin only command.</b>")
    return False

def _get_target(message: types.Message):
    """Gets target user from reply or returns None."""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    return None


@router.message(Command("ban"))
async def cmd_ban(message: types.Message):
    """Ban a user. Reply to their message with /ban."""
    if not await _require_admin(message): return
    target = _get_target(message)
    if not target:
        return await message.answer("↩️ Reply to a user's message to ban them.")
    try:
        await message.bot.ban_chat_member(message.chat.id, target.id)
        await message.answer(f"🚫 <b>{target.full_name}</b> has been <b>banned</b>.")
        try: await message.delete()
        except: pass
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("unban"))
async def cmd_unban(message: types.Message):
    """Unban a user by user_id: /unban <user_id>"""
    if not await _require_admin(message): return
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Usage: <code>/unban user_id</code>")
    try:
        uid = int(args[1])
        await message.bot.unban_chat_member(message.chat.id, uid, only_if_banned=True)
        await message.answer(f"✅ User <code>{uid}</code> has been <b>unbanned</b>.")
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("kick"))
async def cmd_kick(message: types.Message):
    """Kick (ban+unban) a user. Reply with /kick."""
    if not await _require_admin(message): return
    target = _get_target(message)
    if not target:
        return await message.answer("↩️ Reply to a user's message to kick them.")
    try:
        await message.bot.ban_chat_member(message.chat.id, target.id)
        await asyncio.sleep(0.5)
        await message.bot.unban_chat_member(message.chat.id, target.id, only_if_banned=True)
        await message.answer(f"👢 <b>{target.full_name}</b> has been <b>kicked</b>.")
        try: await message.delete()
        except: pass
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("mute"))
async def cmd_mute(message: types.Message):
    """Mute a user. Reply with /mute or /mute 30 (minutes)."""
    if not await _require_admin(message): return
    target = _get_target(message)
    if not target:
        return await message.answer("↩️ Reply to a user's message to mute them.")

    args = message.text.split()
    duration = None
    reply = "permanently"
    if len(args) >= 2:
        try:
            mins = int(args[1])
            duration = datetime.datetime.now() + datetime.timedelta(minutes=mins)
            reply = f"for {mins} minute(s)"
        except ValueError:
            pass

    try:
        await message.bot.restrict_chat_member(
            message.chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=duration
        )
        await message.answer(f"🔇 <b>{target.full_name}</b> has been <b>muted</b> {reply}.")
        try: await message.delete()
        except: pass
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("unmute"))
async def cmd_unmute(message: types.Message):
    """Unmute a user. Reply with /unmute."""
    if not await _require_admin(message): return
    target = _get_target(message)
    if not target:
        return await message.answer("↩️ Reply to a user's message to unmute them.")
    await _unmute_user(message.bot, message.chat.id, target.id)
    await message.answer(f"🔊 <b>{target.full_name}</b> has been <b>unmuted</b>.")
    try: await message.delete()
    except: pass


@router.message(Command("warn"))
async def cmd_warn(message: types.Message):
    """Warn a user. After 3 warns → auto-ban. Reply with /warn."""
    if not await _require_admin(message): return
    target = _get_target(message)
    if not target:
        return await message.answer("↩️ Reply to a user's message to warn them.")

    chat_id = message.chat.id
    warn_count[chat_id][target.id] += 1
    warns = warn_count[chat_id][target.id]

    if warns >= MAX_WARNS:
        try:
            await message.bot.ban_chat_member(chat_id, target.id)
            await message.answer(
                f"🚫 <b>{target.full_name}</b> reached {MAX_WARNS} warnings and was <b>auto-banned</b>."
            )
            warn_count[chat_id][target.id] = 0
        except Exception as e:
            await message.answer(f"❌ Ban error: {e}")
    else:
        await message.answer(
            f"⚠️ <b>{target.full_name}</b> has been warned.\n"
            f"<i>Warnings: {warns}/{MAX_WARNS}</i>\n"
            f"Reaching {MAX_WARNS} will result in a ban."
        )
    try: await message.delete()
    except: pass


@router.message(Command("warnlist"))
async def cmd_warnlist(message: types.Message):
    """Shows all warned users in the group."""
    if not await _require_admin(message): return
    chat_id = message.chat.id
    warns = warn_count.get(chat_id, {})
    if not warns:
        return await message.answer("✅ No warnings in this group.")
    lines = [f"• <code>{uid}</code>: {count} warn(s)" for uid, count in warns.items() if count > 0]
    await message.answer("<b>⚠️ Warned Users:</b>\n\n" + "\n".join(lines) if lines else "✅ No warnings.")


@router.message(Command("purge"))
async def cmd_purge(message: types.Message):
    """Delete the last N messages. Usage: /purge 10"""
    if not await _require_admin(message): return
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Usage: <code>/purge 10</code>")
    try:
        count = int(args[1])
        count = min(count, 100)  # Safety cap
        deleted = 0
        # Get message IDs around current message
        msg_id = message.message_id
        ids_to_delete = list(range(msg_id - count, msg_id + 1))
        for mid in ids_to_delete:
            try:
                await message.bot.delete_message(message.chat.id, mid)
                deleted += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass
        confirm = await message.answer(f"🗑️ Purged <b>{deleted}</b> messages.")
        await asyncio.sleep(3)
        try: await confirm.delete()
        except: pass
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("lock"))
async def cmd_lock(message: types.Message):
    """Locks the group — no messages from regular users."""
    if not await _require_admin(message): return
    locked_chats.add(message.chat.id)
    await message.answer(
        "🔐 <b>Group is now LOCKED.</b>\n"
        "<i>Only admins can send messages. Use /unlock to open.</i>"
    )


@router.message(Command("unlock"))
async def cmd_unlock(message: types.Message):
    """Unlocks the group — all users can send messages."""
    if not await _require_admin(message): return
    locked_chats.discard(message.chat.id)
    await message.answer(
        "🔓 <b>Group is now UNLOCKED.</b>\n"
        "<i>Members can send messages again.</i>"
    )


@router.message(Command("rules"))
async def show_rules(message: types.Message):
    """Shows group rules."""
    await message.answer(
        "<b>✨ Group Rules ✨</b>\n\n"
        "1. ❤️ <b>Be Respectful</b>: No bad language or fighting.\n"
        "2. 🚫 <b>No Spamming</b>: No repeated or flood messages.\n"
        "3. 🔗 <b>No Links</b>: Don't share links to other channels/bots.\n"
        "4. 📢 <b>No Forwards</b>: Don't forward channel posts here.\n"
        "5. 🛡 <b>Privacy First</b>: Never share personal info.\n"
        "6. 🐹 <b>Stay On Topic</b>: Keep chat related to Hamster Kombat!\n\n"
        "<i>Violations = Warning → Mute → Ban. Let's grow together! 🚀</i>"
    )


@router.message(Command("hi"))
async def say_hi(message: types.Message):
    await message.answer(
        "👋 <b>Hello!</b> The <b>Hamster Group Bot</b> is active and protecting this group! 🛡🚀"
    )


@router.message(Command("adminhelp"))
async def admin_help(message: types.Message):
    """Shows all admin commands."""
    if not await _require_admin(message): return
    await message.answer(
        "<b>🛡 Admin Commands</b>\n\n"
        "<b>Member Control:</b>\n"
        "• /ban — Ban user (reply)\n"
        "• /unban &lt;user_id&gt; — Unban by ID\n"
        "• /kick — Kick user (reply)\n"
        "• /mute [mins] — Mute user (reply)\n"
        "• /unmute — Unmute user (reply)\n"
        "• /warn — Warn user (reply, 3 = auto-ban)\n"
        "• /warnlist — See all warned users\n\n"
        "<b>Chat Control:</b>\n"
        "• /lock — Lock group (admins only)\n"
        "• /unlock — Unlock group\n"
        "• /purge &lt;n&gt; — Delete last N messages\n\n"
        "<b>Info:</b>\n"
        "• /rules — Show group rules\n"
        "• /adminhelp — This menu\n\n"
        "<i>Auto-features: anti-link, anti-flood, anti-forward,\n"
        "5-sec join verification, auto-kick unverified users.</i>"
    )
