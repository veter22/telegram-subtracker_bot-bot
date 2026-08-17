from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ==========================================
# ИНЛАЙН-КЛАВИАТУРЫ
# ==========================================
def get_main_menu() -> InlineKeyboardMarkup:
    btn_list = InlineKeyboardButton(text="📋 Мои подписки", callback_data="menu_list")
    btn_add = InlineKeyboardButton(text="➕ Добавить", callback_data="menu_add")
    btn_stats = InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
    btn_settings = InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")
    btn_faq = InlineKeyboardButton(text="❓ FAQ", callback_data="menu_faq")

    return InlineKeyboardMarkup(inline_keyboard=[
        [btn_list, btn_add],
        [btn_stats, btn_settings],
        [btn_faq]
    ])

def get_back_keyboard() -> InlineKeyboardMarkup:
    btn_back = InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")
    return InlineKeyboardMarkup(inline_keyboard=[[btn_back]])

def get_settings_keyboard() -> InlineKeyboardMarkup:
    btn_currency = InlineKeyboardButton(text="💵 Валюта", callback_data="settings_currency")
    btn_time = InlineKeyboardButton(text="⏰ Уведомления (скоро)", callback_data="settings_time")
    btn_back = InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn_currency, btn_time],
        [btn_back]
    ])

def get_currency_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="₽ Рубль", callback_data="set_curr_₽"),
            InlineKeyboardButton(text="$ Доллар", callback_data="set_curr_$")
        ],
        [
            InlineKeyboardButton(text="€ Евро", callback_data="set_curr_€"),
            InlineKeyboardButton(text="₸ Тенге", callback_data="set_curr_₸")
        ],
        [InlineKeyboardButton(text="🔙 Назад в настройки", callback_data="menu_settings")]
    ])

def get_subs_manage_keyboard(subs: list) -> InlineKeyboardMarkup:
    buttons = []
    for sub_id, name, _, _ in subs:
        buttons.append([
            InlineKeyboardButton(text=f"🗑 Удалить {name}", callback_data=f"del_{sub_id}")
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==========================================
# REPLY-КЛАВИАТУРЫ (нижняя панель)
# ==========================================
def get_reply_menu() -> ReplyKeyboardMarkup:
    btn_list = KeyboardButton(text="📋 Мои подписки")
    btn_add = KeyboardButton(text="➕ Добавить")
    btn_stats = KeyboardButton(text="📊 Статистика")
    btn_settings = KeyboardButton(text="⚙️ Настройки")
    btn_faq = KeyboardButton(text="❓ FAQ")

    return ReplyKeyboardMarkup(
        keyboard=[
            [btn_list, btn_add],
            [btn_stats, btn_settings],
            [btn_faq]
        ],
        resize_keyboard=True
    )