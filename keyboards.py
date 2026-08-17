from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ==========================================
# ГЛАВНОЕ МЕНЮ И НАВИГАЦИЯ
# ==========================================
def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои подписки", callback_data="menu_list"), InlineKeyboardButton(text="➕ Добавить", callback_data="menu_add")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats"), InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")],
        [InlineKeyboardButton(text="❓ FAQ", callback_data="menu_faq")]
    ])

def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]])

def get_reply_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Мои подписки"), KeyboardButton(text="➕ Добавить")],
            [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="❓ FAQ")]
        ], resize_keyboard=True
    )

def get_subs_manage_keyboard(subs: list) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=f"🗑 Удалить {name}", callback_data=f"del_{sub_id}")] for sub_id, name, _, _, _ in subs]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==========================================
# ДОБАВЛЕНИЕ ПОДПИСКИ (КАТЕГОРИИ)
# ==========================================
def get_categories_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Кино и Музыка", callback_data="cat_Стриминг"), InlineKeyboardButton(text="💼 Работа", callback_data="cat_Работа")],
        [InlineKeyboardButton(text="🎮 Игры", callback_data="cat_Игры"), InlineKeyboardButton(text="🏃 Спорт", callback_data="cat_Спорт")],
        [InlineKeyboardButton(text="🌐 Связь и VPN", callback_data="cat_Связь"), InlineKeyboardButton(text="📦 Другое", callback_data="cat_Другое")],
    ])

# ==========================================
# НАСТРОЙКИ
# ==========================================
def get_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Валюта", callback_data="settings_currency")],
        [InlineKeyboardButton(text="⏰ Время уведомлений", callback_data="settings_time")],
        [InlineKeyboardButton(text="📅 За сколько дней", callback_data="settings_days")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]
    ])

def get_currency_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="₽ Рубль", callback_data="set_curr_₽"), InlineKeyboardButton(text="$ Доллар", callback_data="set_curr_$")],
        [InlineKeyboardButton(text="€ Евро", callback_data="set_curr_€"), InlineKeyboardButton(text="₸ Тенге", callback_data="set_curr_₸")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_settings")]
    ])

def get_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="08:00", callback_data="set_time_08:00"), InlineKeyboardButton(text="10:00", callback_data="set_time_10:00")],
        [InlineKeyboardButton(text="14:00", callback_data="set_time_14:00"), InlineKeyboardButton(text="19:00", callback_data="set_time_19:00")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_settings")]
    ])

def get_days_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="В день списания (0)", callback_data="set_days_0")],
        [InlineKeyboardButton(text="За 1 день", callback_data="set_days_1"), InlineKeyboardButton(text="За 3 дня", callback_data="set_days_3")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_settings")]
    ])