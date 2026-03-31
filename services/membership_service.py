import config

async def check_user_membership(bot, user_id):
    """Checks if the user is an admin or a member of the mandatory channel."""
    # 1. Bypass check for Admins
    if user_id in config.ADMIN_IDS:
        return True
        
    # 2. Skip if no channel configured
    if not config.CHANNEL_ID or config.CHANNEL_ID == "PASTE_CHANNEL_ID_HERE":
        return True 

    try:
        member = await bot.get_chat_member(chat_id=config.CHANNEL_ID, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"Membership Check Error: {error_msg}")
        
        # If the bot is not in the channel or ID is wrong, notify Admin
        if "chat not found" in error_msg.lower() or "bot is not a member" in error_msg.lower():
            if user_id in config.ADMIN_IDS:
                print("⚠️ ADMIN NOTICE: Your CHANNEL_ID in .env is incorrect or the bot is not an Admin in that channel.")
        
        return False
