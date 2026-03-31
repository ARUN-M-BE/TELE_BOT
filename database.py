import aiosqlite
import config
import datetime

async def init_db():
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        # User & Search Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_joined INTEGER DEFAULT 0,
                last_checked TIMESTAMP,
                last_search_time TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS pending_deletions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                message_id INTEGER,
                delete_at TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_date TEXT,
                url TEXT,
                query TEXT,
                username TEXT,
                message_id INTEGER
            )
        ''')

        # NEW: Group Settings Table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id INTEGER PRIMARY KEY,
                rules TEXT,
                join_hider INTEGER DEFAULT 1,
                flood_control INTEGER DEFAULT 1,
                welcome_message TEXT
            )
        ''')

        # NEW: Hamster News Cache
        await db.execute('''
            CREATE TABLE IF NOT EXISTS hamster_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                updated_at TIMESTAMP
            )
        ''')

        # NEW: Custom Filters
        await db.execute('''
            CREATE TABLE IF NOT EXISTS filters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                keyword TEXT,
                reply TEXT
            )
        ''')

        # Migration logic
        async with db.execute('PRAGMA table_info(users)') as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
            if 'username' not in columns:
                await db.execute('ALTER TABLE users ADD COLUMN username TEXT')
            if 'last_search_time' not in columns:
                await db.execute('ALTER TABLE users ADD COLUMN last_search_time TIMESTAMP')

        async with db.execute('PRAGMA table_info(search_logs)') as cursor:
            columns = [row[1] for row in await cursor.fetchall()]
            if 'username' not in columns:
                await db.execute('ALTER TABLE search_logs ADD COLUMN username TEXT')

        await db.commit()

async def set_user_joined(user_id: int, username: str, joined: bool):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute(
            'INSERT OR REPLACE INTO users (user_id, username, is_joined, last_checked) VALUES (?, ?, ?, ?)',
            (user_id, username, 1 if joined else 0, datetime.datetime.now())
        )
        await db.commit()

async def get_user_status(user_id: int):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        async with db.execute('SELECT is_joined, last_search_time FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def add_pending_deletion(chat_id: int, message_id: int, delay_minutes: int):
    delete_at = datetime.datetime.now() + datetime.timedelta(minutes=delay_minutes)
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute(
            'INSERT INTO pending_deletions (chat_id, message_id, delete_at) VALUES (?, ?, ?)',
            (chat_id, message_id, delete_at)
        )
        await db.commit()

async def get_expired_deletions():
    now = datetime.datetime.now()
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        async with db.execute('SELECT id, chat_id, message_id FROM pending_deletions WHERE delete_at <= ?', (now,)) as cursor:
            return await cursor.fetchall()

async def remove_deletion(id: int):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute('DELETE FROM pending_deletions WHERE id = ?', (id,))
        await db.commit()

async def update_last_search_time(user_id: int):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute(
            'UPDATE users SET last_search_time = ? WHERE user_id = ?',
            (datetime.datetime.now(), user_id)
        )
        await db.commit()

async def log_search(date: str, url: str, query: str, username: str, message_id: int):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute(
            'INSERT INTO search_logs (search_date, url, query, username, message_id) VALUES (?, ?, ?, ?, ?)',
            (date, url, query, username, message_id)
        )
        await db.commit()

# NEW: Group & News Helpers
async def get_group_settings(chat_id: int):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        async with db.execute('SELECT rules, join_hider, flood_control, welcome_message FROM group_settings WHERE chat_id = ?', (chat_id,)) as cursor:
            return await cursor.fetchone()

async def update_group_rules(chat_id: int, rules: text):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO group_settings (chat_id, rules) VALUES (?, ?)', (chat_id, rules))
        await db.commit()

async def get_hamster_news():
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        async with db.execute('SELECT content FROM hamster_news ORDER BY updated_at DESC LIMIT 1') as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def update_hamster_news(content: str):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute('INSERT INTO hamster_news (content, updated_at) VALUES (?, ?)', (content, datetime.datetime.now()))
        await db.commit()
