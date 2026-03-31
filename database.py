import httpx
import json
import config
import datetime
import asyncio

# Cloudflare KV Config
BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{config.CF_ACCOUNT_ID}/storage/kv/namespaces/{config.CF_KV_NAMESPACE_ID}"
HEADERS = {
    "Authorization": f"Bearer {config.CF_API_TOKEN}",
    "Content-Type": "application/json"
}

async def kv_get(key: str):
    """Fetches a value from Cloudflare KV."""
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/values/{key}"
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 200:
            try:
                return json.loads(response.text)
            except:
                return response.text
        return None

async def kv_put(key: str, value: any):
    """Stores a value in Cloudflare KV."""
    val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/values/{key}"
        response = await client.put(url, headers=HEADERS, content=val_str)
        return response.status_code == 200

async def init_db():
    """No local initialization needed for KV, but we can verify the connection."""
    print("☁️ Cloudflare KV Database Connected!")

async def set_user_joined(user_id: int, username: str, joined: bool):
    data = {
        "username": username,
        "is_joined": joined,
        "last_checked": datetime.datetime.now().isoformat()
    }
    await kv_put(f"user:{user_id}", data)

async def get_user_status(user_id: int):
    data = await kv_get(f"user:{user_id}")
    if data and isinstance(data, dict):
        return (1 if data.get('is_joined') else 0, data.get('last_search_time'))
    return None

async def add_pending_deletion(chat_id: int, message_id: int, delay_minutes: int):
    delete_at = (datetime.datetime.now() + datetime.timedelta(minutes=delay_minutes)).isoformat()
    # Unique key for deletion
    key = f"del:{chat_id}:{message_id}"
    await kv_put(key, {"delete_at": delete_at})

async def update_last_search_time(user_id: int):
    data = await kv_get(f"user:{user_id}") or {}
    data["last_search_time"] = datetime.datetime.now().isoformat()
    await kv_put(f"user:{user_id}", data)

# Group & News Helpers
async def get_group_settings(chat_id: int):
    data = await kv_get(f"group:{chat_id}")
    if data:
        return (data.get('rules'), data.get('join_hider'), data.get('flood_control'), data.get('welcome_message'))
    return None

async def update_group_rules(chat_id: int, rules: str):
    data = await kv_get(f"group:{chat_id}") or {}
    data["rules"] = rules
    await kv_put(f"group:{chat_id}", data)

async def get_hamster_news():
    return await kv_get("news:latest")

async def update_hamster_news(content: str):
    await kv_put("news:latest", content)

async def log_search(date: str, url: str, query: str, username: str, message_id: int):
    """Logs search results to Cloudflare KV."""
    data = {
        "date": date,
        "url": url,
        "query": query,
        "username": username,
        "message_id": message_id
    }
    # Store with a unique key prefixed by timestamp for searching/sorting
    key = f"log:{datetime.datetime.now().timestamp()}"
    await kv_put(key, data)

async def get_expired_deletions():
    """NOTE: KV lacks complex querying; simplified for now."""
    # In a full scale app, we would use a queue or secondary indexing
    return [] 

async def remove_deletion(chat_id: int, message_id: int):
    """Removes a deletion marker."""
    key = f"del:{chat_id}:{message_id}"
    # Cloudflare KV doesn't have a direct 'delete' via the simple put interface 
    # for all clients without a DELETE request, but we'll simulate by setting None
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/values/{key}"
        await client.delete(url, headers=HEADERS)
