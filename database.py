import aiosqlite
from datetime import datetime


DATABASE_NAME = "restaurant.db"


async def init_database():
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                payer_id INTEGER,
                currency TEXT NOT NULL DEFAULT 'RSD',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (payer_id) REFERENCES users(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_members (
                session_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (session_id, user_id),
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS item_members (
                item_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (item_id, user_id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                telegram_file_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        await db.commit()


async def create_user(telegram_id: int, name: str):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute(
            """
            INSERT OR IGNORE INTO users
            (telegram_id, name, created_at)
            VALUES (?, ?, ?)
            """,
            (
                telegram_id,
                name,
                datetime.now().isoformat()
            )
        )

        await db.commit()

        cursor = await db.execute(
            """
            SELECT id, telegram_id, name
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        return await cursor.fetchone()


async def get_user(telegram_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute(
            """
            SELECT id, telegram_id, name, created_at
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        return await cursor.fetchone()


async def create_session(
    title: str,
    created_by: int,
    currency: str = "RSD"
):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        created_at = datetime.now().isoformat()
        date = datetime.now().strftime("%Y-%m-%d")

        cursor = await db.execute(
            """
            INSERT INTO sessions
            (
                title,
                date,
                created_by,
                currency,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                date,
                created_by,
                currency,
                "active",
                created_at
            )
        )

        await db.commit()

        return cursor.lastrowid


async def add_session_member(
    session_id: int,
    user_id: int
):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO session_members
            (session_id, user_id)
            VALUES (?, ?)
            """,
            (
                session_id,
                user_id
            )
        )

        await db.commit()


async def add_item(
    session_id: int,
    name: str,
    price: float
):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO items
            (
                session_id,
                name,
                price
            )
            VALUES (?, ?, ?)
            """,
            (
                session_id,
                name,
                price
            )
        )

        await db.commit()

        return cursor.lastrowid


async def add_item_member(
    item_id: int,
    user_id: int
):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO item_members
            (item_id, user_id)
            VALUES (?, ?)
            """,
            (
                item_id,
                user_id
            )
        )

        await db.commit()


async def add_receipt(
    session_id: int,
    telegram_file_id: str
):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            """
            INSERT INTO receipts
            (
                session_id,
                telegram_file_id,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                session_id,
                telegram_file_id,
                datetime.now().isoformat()
            )
        )

        await db.commit()