import os
import asyncio
try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import AudioPiped, VideoPiped
    from pytgcalls.types.stream import StreamAudioQuality, StreamVideoQuality
    HAS_PYTGCALLS = True
except ImportError:
    HAS_PYTGCALLS = False
import config

# Initialize Pyrogram Userbot
# You must provide API_ID and API_HASH from my.telegram.org in your .env
userbot = Client(
    "broadcaster",
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

# Initialize PyTgCalls
if HAS_PYTGCALLS:
    call_py = PyTgCalls(userbot)
else:
    call_py = None

async def start_streaming(chat_id, stream_url, video=True):
    """Starts streaming video/audio into the specified chat's Voice Chat."""
    if not HAS_PYTGCALLS:
        print("❌ Error: pytgcalls is not installed. Video/Audio streaming is disabled.")
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
            
        await call_py.join_group_call(chat_id, stream)
        return True
    except Exception as e:
        print(f"Streaming Error: {e}")
        return False

async def stop_streaming(chat_id):
    """Stops the current stream."""
    if not HAS_PYTGCALLS:
        return False
    try:
        await call_py.leave_group_call(chat_id)
        return True
    except Exception as e:
        print(f"Stop Error: {e}")
        return False

# Initialize the Userbot & PyTgCalls client
async def init_streamer():
    await userbot.start()
    if HAS_PYTGCALLS:
        await call_py.start()
        print("Streamer (Userbot) is now active and ready to join Video Chats!")
    else:
        print("Streamer (Userbot) started without voice chat support (pytgcalls missing).")
