import asyncio
import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.session.aiohttp import AiohttpSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
    await message.answer("Настраиваю меню... ⚙️", reply_markup=keyboards.get_reply_menu())
    await message.answer(
        "👋 Добро пожаловать в **SubTracker**!\n\nВыберите действие:",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "menu_main")
async def cb_back_to_main(callback: types.CallbackQuery, state: FSMContext):
    # Очищаем состояния на случай, если мы нажали "Назад" в процессе добавления
    await state.clear()
    await callback.message.edit_text(
        "👋 Добро пожаловать в **SubTracker**!\n\nВыберите действие:",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==========================================
# БЕСШОВНОЕ ДОБАВЛЕНИЕ ПОДПИСКИ
# ==========================================
@dp.message(Command("add"))
@dp.message(F.text == "➕ Добавить")
async def cmd_add(message: types.Message, state: FSMContext):
    # Удаляем сообщение пользователя
    try: await message.delete()
    except Exception: pass
    
    msg = await message.answer(
        "✍️ Напиши название сервиса (например: Netflix, Яндекс.Плюс):",
        reply_markup=keyboards.get_back_keyboard()
    )
    # Запоминаем ID этого сообщения, чтобы редактировать его дальше
    await state.update_data(main_msg_id=msg.message_id)
    await state.set_state(AddSubscription.waiting_for_name)

@dp.callback_query(F.data == "menu_add")
async def cb_add_subscription(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✍️ Напиши название сервиса (например: Netflix, Яндекс.Плюс):",
        reply_markup=keyboards.get_back_keyboard()
    )
    # Запоминаем ID инлайн-сообщения
    await state.update_data(main_msg_id=callback.message.message_id)
    await state.set_state(AddSubscription.waiting_for_name)
    await callback.answer()

@dp.message(AddSubscription.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    
    # Удаляем текст, который ввел пользователь, чтобы не засорять чат
    try: await message.delete()
    except Exception: pass
    
    # Обновляем наше сохраненное сообщение
    await bot.edit_message_text(
        text=f"Отлично, сервис **{message.text}**.\nСколько он стоит в месяц? (число, например: 299 или 15.50)",
        chat_id=message.chat.id,
        message_id=data['main_msg_id'],
        parse_mode="Markdown",
        reply_markup=keyboards.get_back_keyboard()
    )
    await state.set_state(AddSubscription.waiting_for_price)

@dp.message(AddSubscription.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    data = await state.get_data()
    
    try: await message.delete()
    except Exception: pass
    
    await bot.edit_message_text(
        text="Какого числа каждого месяца происходит списание? (от 1 до 31):",
        chat_id=message.chat.id,
        message_id=data['main_msg_id'],
        reply_markup=keyboards.get_back_keyboard()
    )
    await state.set_state(AddSubscription.waiting_for_date)

@dp.message(AddSubscription.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    sub_name = data['name']
    
    try: await message.delete()
    except Exception: pass
    
    try:
        sub_price = float(data['price'].replace(',', '.'))
        sub_date = int(message.text)
    except ValueError:
        await bot.edit_message_text(
            text="❌ Кажется, в цене или дате была ошибка. Давай попробуем заново:\n\n✍️ Напиши название сервиса:",
            chat_id=message.chat.id,
            message_id=data['main_msg_id'],
            reply_markup=keyboards.get_back_keyboard()
        )
        await state.set_state(AddSubscription.waiting_for_name)
        return
    
    await database.add_subscription(message.from_user.id, sub_name, sub_price, sub_date)
    curr = await database.get_user_currency(message.from_user.id)
    
    # Завершаем диалог и возвращаем главное меню прямо в это же сообщение
    await bot.edit_message_text(
        text=(
            f"✅ **Подписка сохранена!**\n\n"
            f"• Сервис: {sub_name}\n"
            f"• Стоимость: {sub_price:g} {curr}\n"
            f"• День списания: {sub_date}-е число"
        ),
        chat_id=message.chat.id,
        message_id=data['main_msg_id'],
        parse_mode="Markdown",
        reply_markup=keyboards.get_main_menu()
    )
    await state.clear()

# ==========================================
# МОИ ПОДПИСКИ И УДАЛЕНИЕ
# ==========================================
async def get_subs_data(user_id: int):
    subs = await database.get_subscriptions(user_id)
    if not subs:
        return "У тебя пока нет добавленных подписок. Нажми «➕ Добавить», чтобы создать первую!", None
        
    curr = await database.get_user_currency(user_id)
    text = "📋 **Твои активные подписки:**\n\n"
    total_sum = 0
    
    for i, (sub_id, name, price, billing_day) in enumerate(subs, start=1):
        text += f"{i}. **{name}** — {price:g} {curr} (списание {billing_day}-го числа)\n"
        total_sum += price
        
    text += f"\n➖➖➖➖➖➖➖➖➖➖\n💰 **Итого в месяц:** {total_sum:g} {curr}\n\n_Нажми на кнопку ниже, чтобы удалить подписку:_"
    return text, keyboards.get_subs_manage_keyboard(subs)

@dp.message(F.text == "📋 Мои подписки")
async def btn_list_subscriptions(message: types.Message):
    try: await message.delete()
    except Exception: pass
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
    
    text, kb = await get_subs_data(callback.from_user.id)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb or keyboards.get_back_keyboard())

# ==========================================
# СТАТИСТИКА
# ==========================================
async def get_stats_text(user_id: int) -> str:
    subs = await database.get_subscriptions(user_id)
    if not subs:
        return "📊 **Статистика**\n\nНет данных для анализа. Добавь первую подписку!"
    
    curr = await database.get_user_currency(user_id)
    total_sum = sum(sub[2] for sub in subs)
    max_sub = max(subs, key=lambda x: x[2]) 
    
    return (
        f"📊 **Твоя статистика:**\n\n"
        f"📈 Всего подписок: **{len(subs)}**\n"
        f"💰 Общий расход в месяц: **{total_sum:g} {curr}**\n\n"
        f"🔥 Самая дорогая подписка:\n"
        f"• **{max_sub[1]}** — {max_sub[2]:g} {curr}\n\n"
        f"💸 Средний чек подписки: **{(total_sum/len(subs)):.2f} {curr}**"
    )

@dp.message(F.text == "📊 Статистика")
async def btn_stats(message: types.Message):
    try: await message.delete()
    except Exception: pass
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
    try: await message.delete()
    except Exception: pass
    curr = await database.get_user_currency(message.from_user.id)
    await message.answer(
        f"⚙️ **Настройки профиля**\n\n"
        f"💵 Текущая валюта: **{curr}**\n"
        f"⏰ Время уведомлений: **10:00**", 
        parse_mode="Markdown", 
        reply_markup=keyboards.get_settings_keyboard()
    )

@dp.callback_query(F.data == "menu_settings")
async def cb_settings(callback: types.CallbackQuery):
    curr = await database.get_user_currency(callback.from_user.id)
    await callback.message.edit_text(
        f"⚙️ **Настройки профиля**\n\n"
        f"💵 Текущая валюта: **{curr}**\n"
        f"⏰ Время уведомлений: **10:00**", 
        parse_mode="Markdown", 
        reply_markup=keyboards.get_settings_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "settings_currency")
async def cb_settings_currency(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выбери базовую валюту для отображения цен и статистики:",
        reply_markup=keyboards.get_currency_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("set_curr_"))
async def cb_set_currency(callback: types.CallbackQuery):
    selected_currency = callback.data.split("_")[2]
    await database.set_user_currency(callback.from_user.id, selected_currency)
    await callback.answer(f"Валюта изменена на {selected_currency} ✅")
    await cb_settings(callback)

# ==========================================
# FAQ
# ==========================================
async def get_faq_text() -> str:
    return (
        "❓ **Частые вопросы (FAQ)**\n\n"
        "**1. Как добавить подписку?**\n"
        "Нажми кнопку «➕ Добавить» и следуй инструкциям.\n\n"
        "**2. Как работает напоминание?**\n"
        "Каждый день в 10:00 бот проверяет твои подписки и присылает уведомление, если завтра будет списание.\n\n"
        "**3. Как удалить подписку?**\n"
        "Открой «Мои подписки» и нажми кнопку с корзиной под списком."
    )

@dp.message(F.text == "❓ FAQ")
async def btn_faq(message: types.Message):
    try: await message.delete()
    except Exception: pass
    await message.answer(await get_faq_text(), parse_mode="Markdown", reply_markup=keyboards.get_back_keyboard())

@dp.callback_query(F.data == "menu_faq")
async def cb_faq(callback: types.CallbackQuery):
    await callback.message.edit_text(await get_faq_text(), parse_mode="Markdown", reply_markup=keyboards.get_back_keyboard())
    await callback.answer()

# ==========================================
# ФОНОВЫЕ УВЕДОМЛЕНИЯ
# ==========================================
async def check_and_send_reminders(bot: Bot):
    tomorrow = datetime.now() + timedelta(days=1)
    target_day = tomorrow.day
    
    subs = await database.get_subscriptions_by_day(target_day)
    
    for user_id, name, price in subs:
        curr = await database.get_user_currency(user_id)
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"⚠️ **Напоминание о списании!**\n\n"
                    f"Завтра ({target_day}-го числа) с твоей карты спишется **{price:g} {curr}** за сервис **{name}**.\n\n"
                    f"Если подписка больше не нужна, самое время её отменить!"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

# ==========================================
# ЗАПУСК БОТА И ПЛАНИРОВЩИКА
# ==========================================
async def main():
    logging.basicConfig(level=logging.INFO)
    await database.init_db()
    
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(
        check_and_send_reminders, 
        trigger='cron', 
        hour=10, 
        minute=0, 
        kwargs={'bot': bot}
    )
    scheduler.start()
    
    print("SubTracker и планировщик уведомлений запущены...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")