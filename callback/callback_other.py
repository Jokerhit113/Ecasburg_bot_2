from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from keyboard.admins_inline_keyboard import kb_admin_main

callback_other_router = Router()

@callback_other_router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        inline_message_id=callback.inline_message_id,
        text=f"ПАНЕЛЬ АДМИНИСТРАТОРА",
        reply_markup=kb_admin_main)
    await callback.answer("Вы вернулись в меню администратора")


@callback_other_router.callback_query(F.data == "back_to_menu_main")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        text=f"ПАНЕЛЬ АДМИНИСТРАТОРА",
        reply_markup=kb_admin_main)
    await callback.answer("Вы вернулись в меню администратора")