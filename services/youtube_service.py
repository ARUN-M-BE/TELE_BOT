from googleapiclient.discovery import build
import config

def search_youtube(query):
    """
    Searches YouTube for the first video matching the query.
    Returns the video URL and title.
    """
    try:
        youtube = build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)
        
        request = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=1,
            type="video"
        )
        
        response = request.execute()
        
        if response["items"]:
            video_id = response["items"][0]["id"]["videoId"]
            title = response["items"][0]["snippet"]["title"]
            return f"https://www.youtube.com/watch?v={video_id}", title
    except Exception as e:
        # Fallback to a manual search link if the API key has restrictions or fails
        print(f"YouTube API Error: {e}")
        return "https://www.youtube.com/results?search_query=" + query.replace(" ", "+"), query
    
    return None, None
