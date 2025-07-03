from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from keyboard.admins_inline_keyboard import kb_admin_main

callback_other_router = Router()

@callback_other_router.callback_query(F.data == "back_to_menu")
async def back_to_menu(bot: Bot, callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"ПАНЕЛЬ АДМИНИСТРАТОРА",
        reply_markup=kb_admin_main)
    await callback.answer("Вы вернулись в меню администратора")