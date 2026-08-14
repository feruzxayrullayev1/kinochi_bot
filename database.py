import aiosqlite
from datetime import datetime, timedelta

DB_NAME = "kino_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                joined_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                title TEXT,
                invite_link TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS storage_channels (
                type TEXT PRIMARY KEY,          -- 'public' yoki 'premium'
                channel_id TEXT,
                title TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                code TEXT PRIMARY KEY,
                file_id TEXT,
                caption TEXT,
                is_premium INTEGER DEFAULT 0,
                added_at TEXT,
                views INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                method TEXT,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_income INTEGER DEFAULT 0
            )
        """)
        await db.execute("INSERT OR IGNORE INTO stats (id, total_income) VALUES (1, 0)")
        await db.commit()

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, joined_at) VALUES (?, ?, ?, ?)",
            (user_id, username, full_name, datetime.now().isoformat())
        )
        await db.commit()

async def is_premium(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT is_premium, premium_until FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            is_prem, until = row
            if is_prem and until:
                if datetime.fromisoformat(until) > datetime.now():
                    return True
                await db.execute("UPDATE users SET is_premium = 0 WHERE user_id = ?", (user_id,))
                await db.commit()
            return False

async def set_premium(user_id: int, days: int = 30):
    until = (datetime.now() + timedelta(days=days)).isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?",
            (until, user_id)
        )
        await db.commit()

async def add_channel(channel_id: str, title: str, invite_link: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO channels (channel_id, title, invite_link) VALUES (?, ?, ?)",
            (channel_id, title, invite_link)
        )
        await db.commit()

async def remove_channel(channel_id: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        await db.commit()

async def get_channels():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT channel_id, title, invite_link FROM channels") as cursor:
            return await cursor.fetchall()

async def set_storage_channel(type_: str, channel_id: str, title: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO storage_channels (type, channel_id, title) VALUES (?, ?, ?)",
            (type_, channel_id, title)
        )
        await db.commit()

async def get_storage_channel(type_: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT channel_id, title FROM storage_channels WHERE type = ?", (type_,)
        ) as cursor:
            return await cursor.fetchone()

async def add_video(code: str, file_id: str, caption: str = "", is_premium: int = 0):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO videos (code, file_id, caption, is_premium, added_at) VALUES (?, ?, ?, ?, ?)",
            (code, file_id, caption, is_premium, datetime.now().isoformat())
        )
        await db.commit()

async def get_video(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT file_id, caption, is_premium FROM videos WHERE code = ?", (code,)
        ) as cursor:
            return await cursor.fetchone()

async def increment_video_view(code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE videos SET views = views + 1 WHERE code = ?", (code,))
        await db.commit()

async def add_payment(user_id: int, amount: int, method: str = "manual"):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO payments (user_id, amount, method, created_at) VALUES (?, ?, ?, ?)",
            (user_id, amount, method, datetime.now().isoformat())
        )
        await db.execute("UPDATE stats SET total_income = total_income + ? WHERE id = 1", (amount,))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c:
            users = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1") as c:
            premium = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM videos") as c:
            videos = (await c.fetchone())[0]
        async with db.execute("SELECT SUM(views) FROM videos") as c:
            views = (await c.fetchone())[0] or 0
        async with db.execute("SELECT total_income FROM stats WHERE id = 1") as c:
            row = await c.fetchone()
            income = row[0] if row else 0
        return {
            "users": users,
            "premium": premium,
            "videos": videos,
            "views": views,
            "income": income
        }

async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            return await cursor.fetchall()