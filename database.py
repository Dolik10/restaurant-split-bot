import aiosqlite
from datetime import datetime


DATABASE_NAME = "restaurant.db"


# ============================================================
# ПОДКЛЮЧЕНИЕ К БАЗЕ
# ============================================================

async def get_db():
    return await aiosqlite.connect(DATABASE_NAME)


# ============================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ
# ============================================================

async def init_database():
    async with aiosqlite.connect(DATABASE_NAME) as db:

        # ----------------------------------------------------
        # ПОЛЬЗОВАТЕЛИ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                username TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # ----------------------------------------------------
        # РЕСТОРАНЫ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ----------------------------------------------------
        # ПОСИДЕЛКИ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                payer_id INTEGER,
                currency TEXT NOT NULL DEFAULT 'RSD',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,

                FOREIGN KEY (restaurant_id)
                    REFERENCES restaurants(id),

                FOREIGN KEY (created_by)
                    REFERENCES users(id),

                FOREIGN KEY (payer_id)
                    REFERENCES users(id)
            )
        """)

        # ----------------------------------------------------
        # УЧАСТНИКИ ПОСИДЕЛКИ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_members (
                session_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                PRIMARY KEY (session_id, user_id),

                FOREIGN KEY (session_id)
                    REFERENCES sessions(id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
        """)

        # ----------------------------------------------------
        # ПОЗИЦИИ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TEXT NOT NULL,

                FOREIGN KEY (session_id)
                    REFERENCES sessions(id)
            )
        """)

        # ----------------------------------------------------
        # КТО ЕЛ ПОЗИЦИЮ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS item_members (
                item_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                PRIMARY KEY (item_id, user_id),

                FOREIGN KEY (item_id)
                    REFERENCES items(id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
        """)

        # ----------------------------------------------------
        # ОПЛАТЫ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL,

                FOREIGN KEY (session_id)
                    REFERENCES sessions(id),

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
        """)

        # ----------------------------------------------------
        # ЧЕКИ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                telegram_file_id TEXT NOT NULL,
                created_at TEXT NOT NULL,

                FOREIGN KEY (session_id)
                    REFERENCES sessions(id)
            )
        """)

        # ----------------------------------------------------
        # ДОЛГИ
        # ----------------------------------------------------

        await db.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                debtor_id INTEGER NOT NULL,
                creditor_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL,

                FOREIGN KEY (session_id)
                    REFERENCES sessions(id),

                FOREIGN KEY (debtor_id)
                    REFERENCES users(id),

                FOREIGN KEY (creditor_id)
                    REFERENCES users(id)
            )
        """)

        await db.commit()

    await seed_default_restaurants()


# ============================================================
# ПОЛЬЗОВАТЕЛИ
# ============================================================

async def create_user(
    telegram_id: int,
    name: str,
    username: str | None = None
):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        await db.execute(
            """
            INSERT OR IGNORE INTO users
            (
                telegram_id,
                name,
                username,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                telegram_id,
                name,
                username,
                datetime.now().isoformat()
            )
        )

        await db.commit()

        cursor = await db.execute(
            """
            SELECT
                id,
                telegram_id,
                name,
                username,
                created_at
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
            SELECT
                id,
                telegram_id,
                name,
                username,
                created_at
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        return await cursor.fetchone()


async def get_all_users():
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                id,
                telegram_id,
                name,
                username
            FROM users
            ORDER BY name
            """
        )

        return await cursor.fetchall()


async def get_user_by_id(user_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                id,
                telegram_id,
                name,
                username
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        return await cursor.fetchone()


# ============================================================
# РЕСТОРАНЫ
# ============================================================

async def create_restaurant(name: str):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        await db.execute(
            """
            INSERT OR IGNORE INTO restaurants
            (
                name,
                created_at
            )
            VALUES (?, ?)
            """,
            (
                name,
                datetime.now().isoformat()
            )
        )

        await db.commit()

        cursor = await db.execute(
            """
            SELECT
                id,
                name,
                created_at
            FROM restaurants
            WHERE name = ?
            """,
            (name,)
        )

        return await cursor.fetchone()


async def get_restaurant(restaurant_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                id,
                name,
                created_at
            FROM restaurants
            WHERE id = ?
            """,
            (restaurant_id,)
        )

        return await cursor.fetchone()


async def get_restaurant_by_name(name: str):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                id,
                name,
                created_at
            FROM restaurants
            WHERE LOWER(name) = LOWER(?)
            """,
            (name,)
        )

        return await cursor.fetchone()


async def get_all_restaurants():
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                id,
                name,
                created_at
            FROM restaurants
            ORDER BY name
            """
        )

        return await cursor.fetchall()


# ============================================================
# ПОСИДЕЛКИ
# ============================================================

async def create_session(
    restaurant_id: int,
    created_by: int,
    currency: str = "RSD"
):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        now = datetime.now()

        cursor = await db.execute(
            """
            INSERT INTO sessions
            (
                restaurant_id,
                date,
                created_by,
                currency,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                restaurant_id,
                now.strftime("%Y-%m-%d"),
                created_by,
                currency,
                "active",
                now.isoformat()
            )
        )

        await db.commit()

        return cursor.lastrowid


async def get_session(session_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                sessions.id,
                restaurants.name,
                sessions.date,
                sessions.created_by,
                sessions.payer_id,
                sessions.currency,
                sessions.status,
                sessions.created_at
            FROM sessions
            JOIN restaurants
                ON restaurants.id = sessions.restaurant_id
            WHERE sessions.id = ?
            """,
            (session_id,)
        )

        return await cursor.fetchone()


async def get_all_sessions():
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                sessions.id,
                restaurants.name,
                sessions.date,
                sessions.currency,
                sessions.status
            FROM sessions
            JOIN restaurants
                ON restaurants.id = sessions.restaurant_id
            ORDER BY sessions.id DESC
            """
        )

        return await cursor.fetchall()


async def get_restaurant_sessions(restaurant_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                sessions.id,
                sessions.date,
                sessions.currency,
                sessions.status
            FROM sessions
            WHERE sessions.restaurant_id = ?
            ORDER BY sessions.id DESC
            """,
            (restaurant_id,)
        )

        return await cursor.fetchall()


# ============================================================
# УЧАСТНИКИ
# ============================================================

async def add_session_member(
    session_id: int,
    user_id: int
):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        await db.execute(
            """
            INSERT OR IGNORE INTO session_members
            (
                session_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                session_id,
                user_id
            )
        )

        await db.commit()


async def get_session_members(session_id: int):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            SELECT
                users.id,
                users.name,
                users.telegram_id
            FROM users
            JOIN session_members
                ON session_members.user_id = users.id
            WHERE session_members.session_id = ?
            ORDER BY users.name
            """,
            (session_id,)
        )

        return await cursor.fetchall()


# ============================================================
# ПОЗИЦИИ
# ============================================================

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
                price,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                name,
                price,
                datetime.now().isoformat()
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
            (
                item_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                item_id,
                user_id
            )
        )

        await db.commit()


# ============================================================
# ОПЛАТЫ
# ============================================================

async def add_payment(
    session_id: int,
    user_id: int,
    amount: float
):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            INSERT INTO payments
            (
                session_id,
                user_id,
                amount,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                amount,
                datetime.now().isoformat()
            )
        )

        await db.commit()

        return cursor.lastrowid


# ============================================================
# ЧЕКИ
# ============================================================

async def add_receipt(
    session_id: int,
    telegram_file_id: str
):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
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

        return cursor.lastrowid


# ============================================================
# ДОЛГИ
# ============================================================

async def add_debt(
    session_id: int,
    debtor_id: int,
    creditor_id: int,
    amount: float
):
    async with aiosqlite.connect(DATABASE_NAME) as db:

        cursor = await db.execute(
            """
            INSERT INTO debts
            (
                session_id,
                debtor_id,
                creditor_id,
                amount,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                debtor_id,
                creditor_id,
                amount,
                datetime.now().isoformat()
            )
        )

        await db.commit()

        return cursor.lastrowid


# ============================================================
# СТАРТОВЫЕ РЕСТОРАНЫ
# ============================================================

async def seed_default_restaurants():

    restaurants = [
        "Токио Сити",
        "The Бык",
        "The Хинкали",
    ]

    async with aiosqlite.connect(DATABASE_NAME) as db:

        for name in restaurants:

            await db.execute(
                """
                INSERT OR IGNORE INTO restaurants
                (
                    name,
                    created_at
                )
                VALUES (?, ?)
                """,
                (
                    name,
                    datetime.now().isoformat()
                )
            )

        await db.commit()