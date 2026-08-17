from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ==========================================
# ИНЛАЙН-КЛАВИАТУРЫ (под сообщениями)
# ==========================================
def get_main_menu() -> InlineKeyboardMarkup:
    # Создаем кнопки
    btn_list = InlineKeyboardButton(text="📋 Мои подписки", callback_data="menu_list")
    btn_add = InlineKeyboardButton(text="➕ Добавить", callback_data="menu_add")
    
    btn_stats = InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
    btn_settings = InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")
    
    btn_faq = InlineKeyboardButton(text="❓ FAQ", callback_data="menu_faq")

    # Собираем их в ряды
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn_list, btn_add],
        [btn_stats, btn_settings],
        [btn_faq]
    ])

def get_back_keyboard() -> InlineKeyboardMarkup:
    # Клавиатура с одной кнопкой "Назад"
    btn_back = InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")
    return InlineKeyboardMarkup(inline_keyboard=[[btn_back]])

def get_settings_keyboard() -> InlineKeyboardMarkup:
    # Клавиатура для раздела настроек
    btn_currency = InlineKeyboardButton(text="💵 Валюта (скоро)", callback_data="settings_currency")
    btn_time = InlineKeyboardButton(text="⏰ Уведомления (скоро)", callback_data="settings_time")
    btn_back = InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn_currency, btn_time],
        [btn_back]
    ])

# ==========================================
# REPLY-КЛАВИАТУРЫ (нижняя панель)
# ==========================================
def get_reply_menu() -> ReplyKeyboardMarkup:
    # Обычные кнопки для нижней панели
    btn_list = KeyboardButton(text="📋 Мои подписки")
    btn_add = KeyboardButton(text="➕ Добавить")
    
    btn_stats = KeyboardButton(text="📊 Статистика")
    btn_settings = KeyboardButton(text="⚙️ Настройки")
    
    btn_faq = KeyboardButton(text="❓ FAQ")

    # Собираем ряды и включаем resize_keyboard
    return ReplyKeyboardMarkup(
        keyboard=[
            [btn_list, btn_add],
            [btn_stats, btn_settings],
            [btn_faq]
        ],
        resize_keyboard=True
    )