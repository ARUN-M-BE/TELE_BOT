# 🎬 Telegram YouTube Archiver Bot

A professional-grade Telegram bot that searches YouTube for videos based on admin queries, saves the results to Google Sheets, and automatically deletes original search messages after 10 minutes.

## ✨ Features
- **Join-to-Unlock**: Requires users to join a specific channel before using the bot.
- **Admin-Only Search**: Restricts search functionality to designated administrator IDs.
- **Persistent Storage**: Uses SQLite to remember user verification status and pending deletions (survives restarts).
- **Google Sheets Integration**: Automatically archives video titles, URLs, and timestamps.
- **Auto-Delete**: Cleans up the chat by removing original search queries after 10 minutes.
- **Rich UI**: Uses HTML formatting and an interactive command menu.

---

## 🛠 Prerequisites
- **Python 3.8+**
- **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
- **Google Cloud Project** with:
  - **YouTube Data API v3** enabled (API Key)
  - **Google Sheets API** enabled (Service Account JSON)

---

## 🚀 Setup Instructions

### 1. Clone & Install
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment
Create a file named **`.env`** in the root directory and fill it with your credentials:
```env
# Telegram
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789             # Your numeric ID from @userinfobot
CHANNEL_URL=https://t.me/your_channel
CHANNEL_ID=-100123456789        # Your numeric Channel ID

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key

# Google Sheets
SHEET_ID=your_google_sheet_id_from_url
SERVICE_ACCOUNT_FILE=your-service-account.json
```

### 3. Setup Google Sheets
- Create a new Google Sheet.
- Share the sheet with the **service account email** (found in your `.json` file) as an "Editor".
- Copy the **Sheet ID** (the long string between `/d/` and `/edit` in the URL) and paste it into `.env`.

---

## 🏃 Running the Bot
```powershell
py bot.py
```

---

## 🎮 Bot Commands
- `/start` - Start the bot and verify membership.
- `/help` - Show usage instructions.
- `/verify` - Manual membership check.

## 📁 Project Structure
- `bot.py`: Main bot logic and background deletion loop.
- `database.py`: SQLite persistence layer.
- `config.py`: Configuration and environment variable loader.
- `services/`:
  - `youtube_service.py`: YouTube API search logic.
  - `sheets_service.py`: Google Sheets API logging logic.
- `.env`: (Private) Secret keys and configuration values.
