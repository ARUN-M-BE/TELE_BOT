import os
import asyncio
import logging
import config

from pyrogram import Client, filters

try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import AudioPiped, VideoPiped
    from pytgcalls.types.stream import StreamAudioQuality, StreamVideoQuality
    HAS_PYTGCALLS = True
except ImportError:
    HAS_PYTGCALLS = False

logger = logging.getLogger("Streamer")

class Streamer:
    def __init__(self):
        self.app = Client(
            "hamster_userbot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            in_memory=False
        )
        self.call_py = None

    async def start(self):
        """Starts the userbot and the pytgcalls task."""
        if not config.API_ID or not config.API_HASH:
            logger.warning("⚠️ Userbot Disabled: API_ID or API_HASH missing in .env")
            return

        try:
            logger.info("⏳ Starting Userbot (Streamer) in background...")
            # We use a non-blocking start. 
            # If it's the first time, it might still prompt for a phone number in the console.
            await self.app.start() 
            
            if HAS_PYTGCALLS:
                self.call_py = PyTgCalls(self.app)
                await self.call_py.start()
                logger.info("✅ Streamer (Userbot) started with Voice Chat support!")
            else:
                logger.warning("⚠️ Streamer started without voice chat (pytgcalls missing).")
        except Exception as e:
            logger.error(f"❌ Userbot Start Error: {e}")
            logger.info("💡 Tip: If it's your first time, you may need to log in manually by running 'py login_userbot.py'.")

    async def start_streaming(self, chat_id, stream_url, video=True):
        """Starts streaming video/audio into the specified chat's Voice Chat."""
        if not HAS_PYTGCALLS or not self.call_py:
            logger.error("❌ Error: Streaming is disabled or not initialized.")
            return False
        try:
            if video:
                stream = VideoPiped(
                    stream_url,
                    AudioPiped(stream_url, StreamAudioQuality.HIGH),
                    StreamVideoQuality.HD_720P
                )
            else:
                stream = AudioPiped(stream_url, StreamAudioQuality.HIGH)
                
            await self.call_py.join_group_call(chat_id, stream)
            return True
        except Exception as e:
            logger.error(f"Streaming Error: {e}")
            return False

    async def stop_streaming(self, chat_id):
        """Stops the current stream."""
        if not self.call_py:
            return False
        try:
            await self.call_py.leave_group_call(chat_id)
            return True
        except Exception as e:
            logger.error(f"Stop Error: {e}")
            return False
