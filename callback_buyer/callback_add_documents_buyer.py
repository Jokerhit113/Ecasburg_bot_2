import logging
from pathlib import Path

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select


callback_add_documents_buyer_router = Router()

@callback_add_documents_buyer_router.callback_query(F.data == "add_documents_buyer")
async def add_documents_buyer_info(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="Инструкция по загрузке документов", callback_data="info_add_documents_buyer")
    builder.button(text="В главное меню", callback_data="back_main_buyer")
    builder.adjust(1)
    await callback.message.edit_text(
        text="Перед загрузкой документов, ознакомьтесь с ИНСТРУКЦИЕЙ",
        reply_markup=builder.as_markup()

    )

@callback_add_documents_buyer_router.callback_query(F.data == "info_add_documents_buyer")
async def info_add_documents_buyer_info(callback: CallbackQuery):
    file = Path(f"setting/info_load_documents")
    text = file.read_text(encoding='utf-8')
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="add_documents_buyer")
    builder.adjust(1)
    await callback.message.edit_text(
        text=text,
        reply_markup=builder.as_markup())

