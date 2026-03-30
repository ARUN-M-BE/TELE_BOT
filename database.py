import aiosqlite
import config
import datetime

async def init_db():
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_joined INTEGER DEFAULT 0,
                last_checked TIMESTAMP
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
        await db.commit()

async def set_user_joined(user_id: int, joined: bool):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        await db.execute(
            'INSERT OR REPLACE INTO users (user_id, is_joined, last_checked) VALUES (?, ?, ?)',
            (user_id, 1 if joined else 0, datetime.datetime.now())
        )
        await db.commit()

async def get_user_status(user_id: int):
    async with aiosqlite.connect(config.DATABASE_NAME) as db:
        async with db.execute('SELECT is_joined FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return bool(row[0]) if row else None

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
