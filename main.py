import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Описываем шаги (состояния) для добавления подписки
class AddSubscription(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_date = State()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я SubTracker — твой менеджер подписок 🧊\n\n"
        "Я помогу отследить, куда утекают деньги.\n"
        "Введи /add, чтобы добавить подписку!"
    )

# Шаг 1: Запуск команды /add
@dp.message(Command("add"))
async def cmd_add(message: types.Message, state: FSMContext):
    await message.answer("Напиши название сервиса (например: Netflix, Яндекс.Плюс):")
    await state.set_state(AddSubscription.waiting_for_name)

# Шаг 2: Ловим название и спрашиваем цену
@dp.message(AddSubscription.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"Отлично, сервис **{message.text}**.\nСколько он стоит в месяц? (просто число, например: 299 или 15.50)", parse_mode="Markdown")
    await state.set_state(AddSubscription.waiting_for_price)

# Шаг 3: Ловим цену и спрашиваем дату списания
@dp.message(AddSubscription.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Какого числа каждого месяца происходит списание? (введи число от 1 до 31):")
    await state.set_state(AddSubscription.waiting_for_date)

# Шаг 4: Ловим дату, сохраняем и завершаем диалог
@dp.message(AddSubscription.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    sub_name = user_data['name']
    sub_price = user_data['price']
    sub_date = message.text
    
    # Здесь позже мы добавим сохранение в базу данных
    
    await message.answer(
        f"✅ **Подписка сохранена!**\n\n"
        f"• Сервис: {sub_name}\n"
        f"• Стоимость: {sub_price}\n"
        f"• День списания: {sub_date}-е число",
        parse_mode="Markdown"
    )
    # Сбрасываем состояние
    await state.clear()

async def main():
    logging.basicConfig(level=logging.INFO)
    print("SubTracker запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")