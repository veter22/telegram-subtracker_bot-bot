import aiosqlite

DB_NAME = "subtracker.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица подписок
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                price REAL,
                billing_day INTEGER
            )
        ''')
        # Таблица пользователей (для хранения настроек)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                currency TEXT DEFAULT '₽'
            )
        ''')
        await db.commit()

async def get_user_currency(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT currency FROM users WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else "₽"

async def set_user_currency(user_id: int, currency: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT INTO users (user_id, currency) 
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET currency = excluded.currency
        ''', (user_id, currency))
        await db.commit()

async def add_subscription(user_id: int, name: str, price: float, billing_day: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO subscriptions (user_id, name, price, billing_day) VALUES (?, ?, ?, ?)",
            (user_id, name, price, billing_day)
        )
        await db.commit()

async def get_subscriptions(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, name, price, billing_day FROM subscriptions WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

async def delete_subscription(sub_id: int, user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM subscriptions WHERE id = ? AND user_id = ?",
            (sub_id, user_id)
        )
        await db.commit()

async def get_subscriptions_by_day(billing_day: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id, name, price FROM subscriptions WHERE billing_day = ?",
            (billing_day,)
        ) as cursor:
            return await cursor.fetchall()