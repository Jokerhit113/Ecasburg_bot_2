from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



kb_admin_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Новый заказ", callback_data="admin_new_order")],
        [InlineKeyboardButton(text="🤑 Все Заказы", callback_data="admin_all_orders")],
        [InlineKeyboardButton(text="➕ Добавить Пользователя", callback_data="add_new_user")],
        [InlineKeyboardButton(text="❌ Удалить Пользователя", callback_data="show_all_users")]
    ]
)

kb_back_to_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в Меню", callback_data="back_to_menu")],
    ]
)


kb_buyer_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать сделку", callback_data="check_deals_buyer")]
    ]
)

kb_broker_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать сделку", callback_data="check_deals_broker")]
    ]
)

kb_provider_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="View my deals", callback_data="check_deals_provider")]
    ]
)

kb_carrier_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать сделку", callback_data="check_deals_carrier")]
    ]
)