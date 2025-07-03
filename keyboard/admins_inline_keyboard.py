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
        [InlineKeyboardButton(text="Выбрать Поставщика", callback_data="1")],
        [InlineKeyboardButton(text="Выбрать Брокера", callback_data="2")],
        [InlineKeyboardButton(text="Выбрать Логиста", callback_data="3")],
        [InlineKeyboardButton(text="Выбрать покупателя", callback_data="4")],
        [InlineKeyboardButton(text="Проверить статус", callback_data="check_status")],
        [InlineKeyboardButton(text="Действия со сделкой", callback_data="6")],
        [InlineKeyboardButton(text="Готов к Выдаче", callback_data="7")],
        [InlineKeyboardButton(text="Завершить Заказ", callback_data="9")],
        [InlineKeyboardButton(text="Удалить Заказ", callback_data="10")],
        [InlineKeyboardButton(text="Назад к списку", callback_data="admin_all_orders_list")]

    ]
)
