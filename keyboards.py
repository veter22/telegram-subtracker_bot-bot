from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_main_menu() -> InlineKeyboardMarkup:
    """Создает главное меню с Inline-кнопками (прикрепляются к сообщению)."""
    # Создаем кнопки
    btn_list = InlineKeyboardButton(text="📋 Мои подписки", callback_data="menu_list")
    btn_add = InlineKeyboardButton(text="➕ Добавить", callback_data="menu_add")
    
    btn_stats = InlineKeyboardButton(text="📊 Статистика", callback_data="menu_stats")
    btn_settings = InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")
    
    btn_faq = InlineKeyboardButton(text="❓ FAQ", callback_data="menu_faq")

    # Собираем их в ряды (список списков)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [btn_list, btn_add],       # Первый ряд (2 кнопки)
        [btn_stats, btn_settings], # Второй ряд (2 кнопки)
        [btn_faq]                  # Третий ряд (1 кнопка по центру)
    ])
    
    return keyboard

def get_reply_menu() -> ReplyKeyboardMarkup:
    """Создает нижнюю (Reply) клавиатуру."""
    
    # Создаем кнопки (текст как на твоем скриншоте)
    btn_profile = KeyboardButton(text="👤 Профиль")
    btn_balance = KeyboardButton(text="💰 Баланс")
    
    btn_purchases = KeyboardButton(text="🛒 Покупки")
    btn_referrals = KeyboardButton(text="👥 Рефералы")
    btn_shop = KeyboardButton(text="🛍️ Магазин")
    
    btn_faq = KeyboardButton(text="❓ FAQ")
    btn_mirrors = KeyboardButton(text="🌐 Зеркала")
    
    btn_proxy = KeyboardButton(text="📌 Прокси для Telegram")

    # Собираем клавиатуру в ряды
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [btn_profile, btn_balance],               # 1 ряд
            [btn_purchases, btn_referrals, btn_shop], # 2 ряд
            [btn_faq, btn_mirrors],                   # 3 ряд
            [btn_proxy]                               # 4 ряд (одна широкая кнопка)
        ],
        resize_keyboard=True, # Делает кнопки компактными (по размеру текста)
        input_field_placeholder="Выберите действие в меню 👇" # Текст в строке ввода
    )
    
    return keyboard