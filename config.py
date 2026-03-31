import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Admin User IDs (list)
ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i]

# Userbot Credentials (for Video Chat)
# Get these from https://my.telegram.org
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH")

# Channel for Membership Check
CHANNEL_URL = os.getenv("CHANNEL_URL")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

# YouTube & Sheets
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SHEET_ID = os.getenv("SHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

# Project Settings
DATABASE_NAME = "bot_data.db"
AUTO_DELETE_MINUTES = 10
NEWS_CHAT_ID = os.getenv("CHANNEL_ID") # Post daily news here
