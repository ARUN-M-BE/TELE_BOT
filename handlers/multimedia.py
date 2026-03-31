from aiogram import Router, types, F
from aiogram.filters import Command
import streamer
from services import anime_service
import config

router = Router()

@router.message(Command("play"))
async def play_video(message: types.Message):
    """Starts a video stream in the group's video chat."""
    # Control by .env admin ID only
    if message.from_user.id not in config.ADMIN_IDS:
        return await message.answer("❌ Error: Access Denied. Only authorized admins can control the stream.")
    
    # Check if a link is provided or use default
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("Please provide a video link. e.g. /play https://example.com/video.mp4")
    
    url = args[1]
    await message.answer("🚀 Starting video stream... Please join the Video Chat!")
    success = await streamer.start_streaming(message.chat.id, url, video=True)
    if not success:
        await message.answer("❌ Error: Failed to start the stream. Check the link or bot permissions.")

@router.message(Command("anime"))
async def anime_stream(message: types.Message):
    """Searches for an anime and starts streaming the episode."""
    if message.from_user.id not in config.ADMIN_IDS:
        return await message.answer("❌ Error: Only authorized admins can broadcast anime.")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("Please provide an anime name. e.g. /anime Naruto")
    
    query = args[1]
    await message.answer(f"🔍 Searching for <b>{query}</b>...")
    
    # Search metadata
    anime_data = await anime_service.search_anime(query)
    if not anime_data:
        return await message.answer("❌ Error: Anime not found or AniList API issue.")
    
    # Get direct stream link (Simulation)
    stream_url = await anime_service.get_stream_url(query)
    
    await message.answer(f"🎬 Now Telecasting: <b>{anime_data['name']}</b>\n\n{anime_data['description'][:200]}...")
    await streamer.start_streaming(message.chat.id, stream_url, video=True)

@router.message(Command("stop"))
async def stop_stream(message: types.Message):
    """Stops the current stream in the group."""
    if message.from_user.id not in config.ADMIN_IDS:
        return
        
    await message.answer("⏹ Stopping the stream...")
    await streamer.stop_streaming(message.chat.id)
