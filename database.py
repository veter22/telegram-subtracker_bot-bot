import aiosqlite

DB_NAME = "subtracker.db"

async def init_db():
    # Создаем таблицу, если ее еще нет
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                price REAL,
                billing_day INTEGER
            )
        ''')
        await db.commit()

async def add_subscription(user_id: int, name: str, price: float, billing_day: int):
    # Добавляем новую подписку в базу
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO subscriptions (user_id, name, price, billing_day) VALUES (?, ?, ?, ?)",
            (user_id, name, price, billing_day)
        )
        await db.commit()

async def get_subscriptions(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT name, price, billing_day FROM subscriptions WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            # Возвращает список кортежей: [('Netflix', 15.5, 12), ('Яндекс', 299.0, 5)]
            return await cursor.fetchall()
