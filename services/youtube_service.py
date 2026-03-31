from googleapiclient.discovery import build
import config
import urllib.request
import re
import json

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
        print(f"YouTube API Error: {e}. Trying fallback scraping...")
        return search_youtube_scraping(query)
    
    return None, None

def search_youtube_scraping(query):
    """
    Search YouTube by scraping the results page (no API key needed).
    """
    try:
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        req = urllib.request.Request(search_url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            html = response.read().decode()
            
            # Extract ytInitialData JSON
            match = re.search(r'ytInitialData\s*=\s*({.+?});', html)
            if not match:
                return f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}", query
            
            data = json.loads(match.group(1))
            
            # Traverse the complex JSON to find the first video
            # contents -> twoColumnSearchResultsRenderer -> primaryContents -> sectionListRenderer -> 
            # contents[0] -> itemSectionRenderer -> contents -> videoRenderer
            
            section_list = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']
            for section in section_list['contents']:
                if 'itemSectionRenderer' in section:
                    for item in section['itemSectionRenderer']['contents']:
                        if 'videoRenderer' in item:
                            video = item['videoRenderer']
                            video_id = video['videoId']
                            title = video['title']['runs'][0]['text']
                            return f"https://www.youtube.com/watch?v={video_id}", title
                            
    except Exception as e:
        print(f"Scraping Fallback Error: {e}")
        return f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}", query
    
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}", query
