import logging
from pathlib import Path

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select


callback_add_documents_buyer_router = Router()


@callback_add_documents_buyer_router.callback_query(F.data == "info_add_documents_buyer")
async def info_add_documents_buyer_info(callback: CallbackQuery):
    file = Path(f"setting/info_load_documents")
    text = file.read_text(encoding='utf-8')
    builder = InlineKeyboardBuilder()
    builder.button(text=f"УДАЛИТЬ СООБЩЕНИЕ", callback_data=f"delete_message")
    builder.adjust(1)

    await callback.message.answer(text=text, reply_markup=builder.as_markup())
    await callback.answer()

@callback_add_documents_buyer_router.callback_query(F.data == "kb_menu_load_docs")
async def kb_menu_load_docs(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="1 Подтвердить Оплату", callback_data="payment_confirmation_buyer")
    builder.button(text="2 Паспорт", callback_data="add_passport")
    builder.button(text="3 Водительское Удостоверение", callback_data="driver_license_load_buyer")
    builder.button(text="4 СНИЛС", callback_data="add_snils_buyer")
    builder.button(text="5 Выписка по валютному счету", callback_data="foreign_currency_account_statement")
    builder.button(text="6 Справка о движении денежных средств по ВС", callback_data="cash_flow_statement")
    builder.button(text="7 Заполнить Анкету", callback_data="fill_out_the_questionnaire")
    builder.button(text="8 Загрузить Скрин с сайта ЭПТС", callback_data="get_elpts_registration")
    builder.button(text="9 Запросить проверку документов", callback_data="request_check_docs_from_the_broker")
    builder.button(text="В главное меню", callback_data="back_main_buyer")
    builder.adjust(1)
    await callback.answer(text="Для Загрузки документов, выберите нужный пункт меню, и строго следуйте инструкциям.",
                          show_alert=True)
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n"
                f"Для Загрузки документов, выберите нужный пункт меню, и строго следуйте инструкциям.",
        reply_markup=builder.as_markup()
    )

@callback_add_documents_buyer_router.callback_query(F.data == "delete_message")
async def delete_message(callback: CallbackQuery):
    await callback.message.delete()
