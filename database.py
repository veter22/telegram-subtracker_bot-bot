import aiosqlite
import os

# Если мы запускаем бота на сервере Amvera (добавим этот флаг позже), 
# сохраняем базу в защищенную папку /data. Иначе — локально.
if os.getenv("AMVERA") == "1":
    DB_NAME = "/data/subtracker.db"
else:
    DB_NAME = "subtracker.db"

async def init_db():


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица подписок
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                price REAL,
                billing_day INTEGER,
                category TEXT DEFAULT 'Другое'
            )
        ''')
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                currency TEXT DEFAULT '₽',
                notif_time TEXT DEFAULT '10:00',
                notif_days INTEGER DEFAULT 1
            )
        ''')
        
        # Блок авто-миграции (добавляем столбцы в существующую базу без потери данных)
        try: await db.execute("ALTER TABLE subscriptions ADD COLUMN category TEXT DEFAULT 'Другое'")
        except Exception: pass
        try: await db.execute("ALTER TABLE users ADD COLUMN notif_time TEXT DEFAULT '10:00'")
        except Exception: pass
        try: await db.execute("ALTER TABLE users ADD COLUMN notif_days INTEGER DEFAULT 1")
        except Exception: pass
        
        await db.commit()

# --- Функции Пользователей ---
async def get_user_settings(user_id: int) -> dict:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT currency, notif_time, notif_days FROM users WHERE user_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            if res:
                return {"currency": res[0], "notif_time": res[1], "notif_days": res[2]}
            # Настройки по умолчанию
            return {"currency": "₽", "notif_time": "10:00", "notif_days": 1}

async def update_user_setting(user_id: int, field: str, value):
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем запись с дефолтными значениями, если её нет, затем обновляем нужное поле
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
        await db.commit()

# --- Функции Подписок ---
async def add_subscription(user_id: int, name: str, price: float, billing_day: int, category: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO subscriptions (user_id, name, price, billing_day, category) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, price, billing_day, category)
        )
        await db.commit()

async def get_subscriptions(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, name, price, billing_day, category FROM subscriptions WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()

async def delete_subscription(sub_id: int, user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM subscriptions WHERE id = ? AND user_id = ?", (sub_id, user_id))
        await db.commit()

async def get_all_users_settings():
    # Нужно для планировщика: получаем настройки всех пользователей
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, notif_time, notif_days, currency FROM users") as cursor:
            return await cursor.fetchall()