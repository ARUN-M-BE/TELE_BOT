import os
from dotenv import load_dotenv

# Load environmental variables from .env file
load_dotenv()

# Telegram Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "0").split(",") if id.strip()]
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/example")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

# YouTube Configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY")

# Google Sheets Configuration
SHEET_ID = os.getenv("SHEET_ID", "YOUR_GOOGLE_SHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "service_account.json")

# Bot settings
AUTO_DELETE_MINUTES = 10
DATABASE_NAME = "bot_data.db"
