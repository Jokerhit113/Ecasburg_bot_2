from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.state_fsm import NewUser

callback_admin_router = Router()
name_get = None
user_id_get = None
departament_get = None

# @callback_admin_router.callback_query(F.data == "add_new_user")
# async def add_new_user_callback(callback: CallbackQuery, bot: Bot):
#     await bot.send_message(
#         chat_id=callback.message.chat.id,
#         text="Напиши команду как указано ниже:\n\n"
#                            "/add_new_user Иван 1265203464 broker\n\n"
#                            "/add_new_user ИМЯ, ID пользователя ТГ, Департамент\n\n"
#                            "Департаменты к использованию:\n"
#                            "admin - Администратор\n"
#                            "provider - Поставщик\n"
#                            "broker - Брокер\n"
#                            "carrier - Перевозчик\n"
#                            "buyer - Покупатель")

@callback_admin_router.callback_query(F.data == "add_new_user")
async def add_new_user_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    await state.set_state(NewUser.waiting_for_departament)
    builder = InlineKeyboardBuilder()
    builder.button(text="Администратор", callback_data="admin")
    builder.button(text="Поставщик", callback_data="provider")
    builder.button(text="Брокер", callback_data="broker")
    builder.button(text="Перевозчик", callback_data="carrier")
    builder.button(text="Покупатель", callback_data="buyer")
    builder.adjust(1)  # Все кнопки в отдельных рядах

    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Кого хотите добавить?", reply_markup=builder.as_markup())

@callback_admin_router.callback_query(NewUser.waiting_for_departament)
async def get_departament(callback: CallbackQuery, bot: Bot, state: FSMContext):
    global departament_get
    departament_get = callback.data
    await bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Укажите Имя Пользователя:",
        reply_markup=None
    )
    await callback.answer()
    await state.set_state(NewUser.waiting_for_name)

@callback_admin_router.message(NewUser.waiting_for_name)
async def get_name_new_user(message: Message, state: FSMContext):
    pass