import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Инициализируем бота и диспетчер
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я SubTracker — твой менеджер подписок 🧊\n\n"
        "Я помогу отследить, куда утекают деньги, и напомню об отмене триалов.\n"
        "Введи /add, чтобы добавить первую подписку!"
    )

async def main():
    # Настраиваем логирование
    logging.basicConfig(level=logging.INFO)
    
    # Запускаем бота
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")