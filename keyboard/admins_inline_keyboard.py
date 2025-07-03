from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



kb_admin_main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Новый заказ", callback_data="admin_new_order")],
        [InlineKeyboardButton(text="Все Заказы", callback_data="admin_all_orders")],
        [InlineKeyboardButton(text="Добавить Пользователя", callback_data="add_new_user")],
        [InlineKeyboardButton(text="Удалить Пользователя", callback_data="show_all_users")]
    ]
)

