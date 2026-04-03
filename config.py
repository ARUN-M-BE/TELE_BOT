import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot API
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(i) for i in os.getenv("ADMIN_IDS", "").split(",") if i]

# Channel for Membership Check
CHANNEL_URL = os.getenv("CHANNEL_URL")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

# Cloudflare Workers KV
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_KV_NAMESPACE_ID = os.getenv("CF_KV_NAMESPACE_ID")
CF_API_TOKEN = os.getenv("CF_API_TOKEN")

# YouTube & Sheets
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SHEET_ID = os.getenv("SHEET_ID")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "api-client-398313-e0620396f1f6.json")
SERVICE_ACCOUNT_JSON = os.getenv("SERVICE_ACCOUNT_JSON")

# Project Settings
AUTO_DELETE_MINUTES = 10
NEWS_CHAT_ID = os.getenv("CHANNEL_ID")
