from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



kb_admin_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Новый заказ", callback_data="admin_new_order")],
        [InlineKeyboardButton(text="Все Заказы", callback_data="admin_all_orders")],
        [InlineKeyboardButton(text="Добавить Пользователя", callback_data="add_new_user")],
        [InlineKeyboardButton(text="Удалить Пользователя", callback_data="show_all_users")]
    ]
)

kb_back_to_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Назад в Меню", callback_data="back_to_menu")],
    ]
)

kb_deal = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Загрузить договор", callback_data="add_contract")],
        [InlineKeyboardButton(text="Выбрать Поставщика", callback_data="change_provider")],
        [InlineKeyboardButton(text="Выбрать Брокера", callback_data="change_broker")],
        [InlineKeyboardButton(text="Выбрать Логиста", callback_data="change_carrier")],
        [InlineKeyboardButton(text="Выбрать покупателя", callback_data="change_buyer")],
        [InlineKeyboardButton(text="Проверить статус", callback_data="check_status")],
        [InlineKeyboardButton(text="Действия со сделкой", callback_data="6")],
        [InlineKeyboardButton(text="Готов к Выдаче", callback_data="7")],
        [InlineKeyboardButton(text="Завершить Заказ", callback_data="9")],
        [InlineKeyboardButton(text="Удалить Заказ", callback_data="delete_deal")],
        [InlineKeyboardButton(text="Назад к списку", callback_data="admin_all_orders_list")]

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