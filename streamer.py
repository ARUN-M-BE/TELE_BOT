import os
import asyncio
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, VideoPiped
from pytgcalls.types.stream import StreamAudioQuality, StreamVideoQuality
import config

# Initialize Pyrogram Userbot
# You must provide API_ID and API_HASH from my.telegram.org in your .env
userbot = Client(
    "broadcaster",
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

# Initialize PyTgCalls
call_py = PyTgCalls(userbot)

async def start_streaming(chat_id, stream_url, video=True):
    """Starts streaming video/audio into the specified chat's Voice Chat."""
    try:
        if video:
            stream = VideoPiped(
                stream_url,
                AudioPiped(stream_url, StreamAudioQuality.HIGH),
                StreamVideoQuality.HD_720P
            )
        else:
            stream = AudioPiped(stream_url, StreamAudioQuality.HIGH)
            
        await call_py.join_group_call(chat_id, stream)
        return True
    except Exception as e:
        print(f"Streaming Error: {e}")
        return False

async def stop_streaming(chat_id):
    """Stops the current stream."""
    try:
        await call_py.leave_group_call(chat_id)
        return True
    except Exception as e:
        print(f"Stop Error: {e}")
        return False

# Initialize the Userbot & PyTgCalls client
async def init_streamer():
    await userbot.start()
    await call_py.start()
    print("Streamer (Userbot) is now active and ready to join Video Chats!")
