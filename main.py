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
    waiting_for_category = State()
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
    await state.clear()
    await callback.message.edit_text(
        "👋 Добро пожаловать в **SubTracker**!\n\nВыберите действие:",
        reply_markup=keyboards.get_main_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==========================================
# ДОБАВЛЕНИЕ ПОДПИСКИ (БЕСШОВНОЕ)
# ==========================================
@dp.message(Command("add"))
@dp.message(F.text == "➕ Добавить")
async def cmd_add(message: types.Message, state: FSMContext):
    try: await message.delete()
    except Exception: pass
    
    msg = await message.answer(
        "✍️ Напиши название сервиса (например: Netflix, Яндекс.Плюс):", 
        reply_markup=keyboards.get_back_keyboard()
    )
    await state.update_data(main_msg_id=msg.message_id)
    await state.set_state(AddSubscription.waiting_for_name)

@dp.callback_query(F.data == "menu_add")
async def cb_add_subscription(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "✍️ Напиши название сервиса (например: Netflix, Яндекс.Плюс):", 
        reply_markup=keyboards.get_back_keyboard()
    )
    await state.update_data(main_msg_id=callback.message.message_id)
    await state.set_state(AddSubscription.waiting_for_name)
    await callback.answer()

@dp.message(AddSubscription.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    try: await message.delete()
    except Exception: pass
    await state.update_data(name=message.text)
    data = await state.get_data()
    await bot.edit_message_text(
        text=f"Отлично, **{message.text}**.\nСколько стоит в месяц? (число)", 
        chat_id=message.chat.id, message_id=data['main_msg_id'], parse_mode="Markdown", reply_markup=keyboards.get_back_keyboard()
    )
    await state.set_state(AddSubscription.waiting_for_price)

@dp.message(AddSubscription.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    try: await message.delete()
    except Exception: pass
    await state.update_data(price=message.text)
    data = await state.get_data()
    await bot.edit_message_text(
        text="К какой категории отнести сервис?", 
        chat_id=message.chat.id, message_id=data['main_msg_id'], reply_markup=keyboards.get_categories_keyboard()
    )
    await state.set_state(AddSubscription.waiting_for_category)

@dp.callback_query(AddSubscription.waiting_for_category, F.data.startswith("cat_"))
async def cb_process_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    await state.update_data(category=category)
    data = await state.get_data()
    
    await bot.edit_message_text(
        text="Какого числа каждого месяца списание? (от 1 до 31):", 
        chat_id=callback.message.chat.id, message_id=data['main_msg_id'], reply_markup=keyboards.get_back_keyboard()
    )
    await state.set_state(AddSubscription.waiting_for_date)
    await callback.answer()

@dp.message(AddSubscription.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    try: await message.delete()
    except Exception: pass
    data = await state.get_data()
    
    try:
        sub_price = float(str(data['price']).replace(',', '.'))
        sub_date = int(message.text)
    except ValueError:
        await bot.edit_message_text(
            text="❌ Ошибка в цене или дате.\nДавай заново.\n\n✍️ Напиши название сервиса:",
            chat_id=message.chat.id, message_id=data['main_msg_id'], reply_markup=keyboards.get_back_keyboard()
        )
        await state.set_state(AddSubscription.waiting_for_name)
        return
    
    await database.add_subscription(message.from_user.id, data['name'], sub_price, sub_date, data['category'])
    settings = await database.get_user_settings(message.from_user.id)
    
    await bot.edit_message_text(
        text=(
            f"✅ **Подписка сохранена!**\n\n"
            f"• Сервис: {data['name']}\n"
            f"• Категория: {data['category']}\n"
            f"• Стоимость: {sub_price:g} {settings['currency']}\n"
            f"• Списание: {sub_date}-го числа"
        ),
        chat_id=message.chat.id, message_id=data['main_msg_id'], parse_mode="Markdown", reply_markup=keyboards.get_main_menu()
    )
    await state.clear()

# ==========================================
# МОИ ПОДПИСКИ
# ==========================================
async def get_subs_data(user_id: int):
    subs = await database.get_subscriptions(user_id)
    if not subs: return "У тебя пока нет подписок. Нажми «➕ Добавить»!", None
        
    s = await database.get_user_settings(user_id)
    curr = s['currency']
    text = "📋 **Твои активные подписки:**\n\n"
    total_sum = 0
    
    for i, (sub_id, name, price, billing_day, category) in enumerate(subs, start=1):
        text += f"{i}. **{name}** ({category}) — {price:g} {curr} (до {billing_day}-го)\n"
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
    if not subs: return "📊 **Статистика**\n\nНет данных для анализа."
    
    s = await database.get_user_settings(user_id)
    curr = s['currency']
    total_sum = 0
    cat_sums = {}
    
    for _, name, price, _, category in subs:
        total_sum += price
        cat_sums[category] = cat_sums.get(category, 0) + price
        
    max_sub = max(subs, key=lambda x: x[2]) 
    
    text = (
        f"📊 **Твоя статистика:**\n\n"
        f"📈 Всего подписок: **{len(subs)}**\n"
        f"💰 Общий расход в месяц: **{total_sum:g} {curr}**\n\n"
        f"🔥 Самая дорогая подписка:\n"
        f"• **{max_sub[1]}** — {max_sub[2]:g} {curr}\n\n"
        f"🗂 **Распределение по категориям:**\n"
    )
    
    # Сортируем категории по сумме и строим прогресс-бары
    sorted_cats = sorted(cat_sums.items(), key=lambda x: x[1], reverse=True)
    for cat, c_sum in sorted_cats:
        percent = (c_sum / total_sum) * 100 if total_sum > 0 else 0
        filled = int(round(percent / 10))
        bar = '█' * filled + '░' * (10 - filled)
        text += f"`{cat:15}`\n`[{bar}] {percent:.0f}%` ({c_sum:g} {curr})\n\n"
        
    return text

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
async def get_settings_text(user_id: int):
    s = await database.get_user_settings(user_id)
    days_str = "В день списания" if s['notif_days'] == 0 else f"За {s['notif_days']} дн."
    return (
        f"⚙️ **Настройки профиля**\n\n"
        f"💵 Валюта: **{s['currency']}**\n"
        f"⏰ Время уведомлений: **{s['notif_time']}**\n"
        f"📅 Срок напоминания: **{days_str}**"
    )

@dp.message(F.text == "⚙️ Настройки")
async def btn_settings(message: types.Message):
    try: await message.delete()
    except Exception: pass
    await message.answer(await get_settings_text(message.from_user.id), parse_mode="Markdown", reply_markup=keyboards.get_settings_keyboard())

@dp.callback_query(F.data == "menu_settings")
async def cb_settings(callback: types.CallbackQuery):
    await callback.message.edit_text(await get_settings_text(callback.from_user.id), parse_mode="Markdown", reply_markup=keyboards.get_settings_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "settings_currency")
async def cb_settings_currency(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери базовую валюту:", reply_markup=keyboards.get_currency_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("set_curr_"))
async def cb_set_currency(callback: types.CallbackQuery):
    val = callback.data.split("_")[2]
    await database.update_user_setting(callback.from_user.id, "currency", val)
    await cb_settings(callback)

@dp.callback_query(F.data == "settings_time")
async def cb_settings_time(callback: types.CallbackQuery):
    await callback.message.edit_text("В какое время присылать уведомления?", reply_markup=keyboards.get_time_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("set_time_"))
async def cb_set_time(callback: types.CallbackQuery):
    val = callback.data.split("_")[2]
    await database.update_user_setting(callback.from_user.id, "notif_time", val)
    await cb_settings(callback)

@dp.callback_query(F.data == "settings_days")
async def cb_settings_days(callback: types.CallbackQuery):
    await callback.message.edit_text("За сколько дней предупреждать о списании?", reply_markup=keyboards.get_days_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("set_days_"))
async def cb_set_days(callback: types.CallbackQuery):
    val = int(callback.data.split("_")[2])
    await database.update_user_setting(callback.from_user.id, "notif_days", val)
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
        "Зайди в «Настройки» и укажи удобное время и срок. Бот сам рассчитает, когда нужно прислать алерт.\n\n"
        "**3. Как посмотреть графики трат?**\n"
        "В разделе «Статистика» бот автоматически рисует прогресс-бары твоих расходов по категориям."
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
    # Запускается каждый час. Получаем текущий час (например, "10:00")
    current_time_str = datetime.now().strftime("%H:00")
    
    # Получаем настройки всех пользователей
    users = await database.get_all_users_settings()
    
    for user_id, notif_time, notif_days, currency in users:
        # Если время пользователя не совпадает с текущим часом — пропускаем
        if notif_time != current_time_str:
            continue
            
        # Вычисляем целевой день (если notif_days=1, значит ищем списания на завтра)
        target_date = datetime.now() + timedelta(days=notif_days)
        target_day = target_date.day
        
        # Берем подписки конкретного пользователя
        subs = await database.get_subscriptions(user_id)
        
        for sub_id, name, price, billing_day, category in subs:
            if billing_day == target_day:
                days_text = "Завтра" if notif_days == 1 else ("Сегодня" if notif_days == 0 else f"Через {notif_days} дня")
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"⚠️ **Напоминание о списании!**\n\n"
                            f"{days_text} ({target_day}-го числа) с твоей карты спишется **{price:g} {currency}** за сервис **{name}**.\n\n"
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
    
    # Теперь планировщик запускается КАЖДЫЙ ЧАС (в 00 минут), а внутри сверяет настройки пользователей
    scheduler.add_job(
        check_and_send_reminders, 
        trigger='cron', 
        hour='*', 
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