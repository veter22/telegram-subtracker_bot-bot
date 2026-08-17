import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

import keyboards
import database

load_dotenv()

# Настройка прокси
session = AiohttpSession(proxy="http://127.0.0.1:10809")
bot = Bot(token=os.getenv('BOT_TOKEN'), session=session)
dp = Dispatcher()

class AddSubscription(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_date = State()

# ==========================================
# СТАРТ И ГЛАВНОЕ МЕНЮ
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Системное сообщение для активации нижней панели (Reply)
    await message.answer("Настраиваю меню... ⚙️", reply_markup=keyboards.get_reply_menu())
    
    # Главное сообщение с инлайн-меню
    await message.answer(
        "👋 Добро пожаловать в **SubTracker**!\n\n"
        "Выберите действие:",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="Markdown"
    )

# Кнопка "Назад" (возвращает главное инлайн-меню)
@dp.callback_query(F.data == "menu_main")
async def cb_back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Добро пожаловать в **SubTracker**!\n\n"
        "Выберите действие:",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==========================================
# ДОБАВЛЕНИЕ ПОДПИСКИ
# ==========================================
@dp.message(Command("add"))
@dp.message(F.text == "➕ Добавить")
async def cmd_add(message: types.Message, state: FSMContext):
    await message.answer("Напиши название сервиса (например: Netflix, Яндекс.Плюс):")
    await state.set_state(AddSubscription.waiting_for_name)

@dp.callback_query(F.data == "menu_add")
async def cb_add_subscription(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer() 
    await callback.message.answer("Напиши название сервиса (например: Netflix, Яндекс.Плюс):")
    await state.set_state(AddSubscription.waiting_for_name)

@dp.message(AddSubscription.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"Отлично, сервис **{message.text}**.\nСколько он стоит в месяц? (просто число, например: 299 или 15.50)", parse_mode="Markdown")
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
    
    try:
        sub_price = float(user_data['price'].replace(',', '.'))
        sub_date = int(message.text)
    except ValueError:
        await message.answer("Кажется, в цене или дате была ошибка. Давай попробуем заново: /add")
        await state.clear()
        return
    
    await database.add_subscription(message.from_user.id, sub_name, sub_price, sub_date)
    
    await message.answer(
        f"✅ **Подписка сохранена в базу!**\n\n"
        f"• Сервис: {sub_name}\n"
        f"• Стоимость: {sub_price}\n"
        f"• День списания: {sub_date}-е число",
        parse_mode="Markdown"
    )
    await state.clear()

# ==========================================
# МОИ ПОДПИСКИ И УДАЛЕНИЕ
# ==========================================
async def get_subs_data(user_id: int):
    subs = await database.get_subscriptions(user_id)
    if not subs:
        return "У тебя пока нет добавленных подписок. Нажми «➕ Добавить», чтобы создать первую!", None
        
    text = "📋 **Твои активные подписки:**\n\n"
    total_sum = 0
    for i, (sub_id, name, price, billing_day) in enumerate(subs, start=1):
        price_str = f"{price:g}" 
        text += f"{i}. **{name}** — {price_str} (списание {billing_day}-го числа)\n"
        total_sum += price
        
    text += f"\n➖➖➖➖➖➖➖➖➖➖\n💰 **Итого в месяц:** {total_sum:g}\n\n_Нажми на кнопку ниже, чтобы удалить подписку:_"
    return text, keyboards.get_subs_manage_keyboard(subs)

@dp.message(F.text == "📋 Мои подписки")
async def btn_list_subscriptions(message: types.Message):
    text, kb = await get_subs_data(message.from_user.id)
    await message.answer(text, parse_mode="Markdown", reply_markup=kb or keyboards.get_back_keyboard())

@dp.callback_query(F.data == "menu_list")
async def cb_list_subscriptions(callback: types.CallbackQuery):
    text, kb = await get_subs_data(callback.from_user.id)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb or keyboards.get_back_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("del_"))
async def cb_delete_subscription(callback: types.CallbackQuery):
    sub_id = int(callback.data.split("_")[1])
    await database.delete_subscription(sub_id, callback.from_user.id)
    await callback.answer("Подписка удалена! 🗑")
    
    # Обновляем сообщение со списком
    text, kb = await get_subs_data(callback.from_user.id)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb or keyboards.get_back_keyboard())

# ==========================================
# СТАТИСТИКА
# ==========================================
async def get_stats_text(user_id: int) -> str:
    subs = await database.get_subscriptions(user_id)
    if not subs:
        return "📊 **Статистика**\n\nНет данных для анализа. Добавь первую подписку!"
    
    total_sum = sum(sub[2] for sub in subs)
    max_sub = max(subs, key=lambda x: x[2]) 
    
    return (
        f"📊 **Твоя статистика:**\n\n"
        f"📈 Всего подписок: **{len(subs)}**\n"
        f"💰 Общий расход в месяц: **{total_sum:g}**\n\n"
        f"🔥 Самая дорогая подписка:\n"
        f"• **{max_sub[1]}** — {max_sub[2]:g}\n\n"
        f"💸 Средний чек подписки: **{(total_sum/len(subs)):.2f}**"
    )

@dp.message(F.text == "📊 Статистика")
async def btn_stats(message: types.Message):
    await message.answer(await get_stats_text(message.from_user.id), parse_mode="Markdown", reply_markup=keyboards.get_back_keyboard())

@dp.callback_query(F.data == "menu_stats")
async def cb_stats(callback: types.CallbackQuery):
    await callback.message.edit_text(await get_stats_text(callback.from_user.id), parse_mode="Markdown", reply_markup=keyboards.get_back_keyboard())
    await callback.answer()

# ==========================================
# НАСТРОЙКИ
# ==========================================
@dp.message(F.text == "⚙️ Настройки")
async def btn_settings(message: types.Message):
    await message.answer("⚙️ **Настройки профиля**\n\nЗдесь скоро можно будет выбрать базовую валюту и время напоминаний.", parse_mode="Markdown", reply_markup=keyboards.get_settings_keyboard())

@dp.callback_query(F.data == "menu_settings")
async def cb_settings(callback: types.CallbackQuery):
    await callback.message.edit_text("⚙️ **Настройки профиля**\n\nЗдесь скоро можно будет выбрать базовую валюту и время напоминаний.", parse_mode="Markdown", reply_markup=keyboards.get_settings_keyboard())
    await callback.answer()

# ==========================================
# FAQ
# ==========================================
async def get_faq_text() -> str:
    return (
        "❓ **Частые вопросы (FAQ)**\n\n"
        "**1. Как добавить подписку?**\n"
        "Нажми кнопку «➕ Добавить» и следуй инструкциям.\n\n"
        "**2. Как бот напомнит о списании?**\n"
        "Скоро мы добавим фоновые уведомления за 24 часа до списания!\n\n"
        "**3. Как удалить подписку?**\n"
        "Открой «Мои подписки» и нажми кнопку с корзиной под списком."
    )

@dp.message(F.text == "❓ FAQ")
async def btn_faq(message: types.Message):
    await message.answer(await get_faq_text(), parse_mode="Markdown", reply_markup=keyboards.get_back_keyboard())

@dp.callback_query(F.data == "menu_faq")
async def cb_faq(callback: types.CallbackQuery):
    await callback.message.edit_text(await get_faq_text(), parse_mode="Markdown", reply_markup=keyboards.get_back_keyboard())
    await callback.answer()

# ==========================================
# ЗАПУСК БОТА
# ==========================================
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