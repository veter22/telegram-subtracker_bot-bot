import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv
from aiogram.client.session.aiohttp import AiohttpSession

import keyboards  # Подключаем наш файл с клавиатурами
import database   # Подключаем нашу базу

load_dotenv()

# Настраиваем прокси для обхода блокировок
session = AiohttpSession(proxy="http://127.0.0.1:10809")
bot = Bot(token=os.getenv('BOT_TOKEN'), session=session)
dp = Dispatcher()

# Класс для пошагового сбора данных о подписке
class AddSubscription(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_date = State()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Сначала отправляем системное сообщение, чтобы показать нижнюю панель (Reply)
    await message.answer(
        "Настраиваю меню... ⚙️",
        reply_markup=keyboards.get_reply_menu()
    )
    
    # А затем уже красивое приветствие с Inline-кнопками
    await message.answer(
        "👋 Добро пожаловать в **SubTracker**!\n\n"
        "Выберите действие:",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="Markdown"
    )

@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    await message.answer("Напиши название сервиса (например: Netflix, Яндекс.Плюс):")
    await state.set_state(AddSubscription.waiting_for_name)

# Обработчик нажатия на кнопку "➕ Добавить" из меню
@dp.callback_query(F.data == "menu_add")
async def cb_add_subscription(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer() # Убираем "часики" загрузки с кнопки
    await callback.message.answer("Напиши название сервиса (например: Netflix, Яндекс.Плюс):")
    await state.set_state(AddSubscription.waiting_for_name)

@dp.message(AddSubscription.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        f"Отлично, сервис **{message.text}**.\n"
        f"Сколько он стоит в месяц? (просто число, например: 299 или 15.50)", 
        parse_mode="Markdown"
    )
    await state.set_state(AddSubscription.waiting_for_price)

@dp.message(AddSubscription.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Какого числа каждого месяца происходит списание? (введи число от 1 до 31):")
    await state.set_state(AddSubscription.waiting_for_date)

@dp.message(AddSubscription.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    sub_name = user_data['name']
    
    # Пробуем перевести цену и дату в числа
    try:
        sub_price = float(user_data['price'].replace(',', '.'))
        sub_date = int(message.text)
    except ValueError:
        await message.answer("Кажется, в цене или дате была ошибка. Давай попробуем заново: /add")
        await state.clear()
        return
    
    # Сохраняем в базу данных
    await database.add_subscription(message.from_user.id, sub_name, sub_price, sub_date)
    
    await message.answer(
        f"✅ **Подписка сохранена в базу!**\n\n"
        f"• Сервис: {sub_name}\n"
        f"• Стоимость: {sub_price}\n"
        f"• День списания: {sub_date}-е число",
        parse_mode="Markdown"
    )
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Инициализируем базу данных перед запуском бота
    await database.init_db()
    
    print("SubTracker запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")