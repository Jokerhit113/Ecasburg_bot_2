import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_buyer_main

callback_check_deals_buyer_router = Router()

@callback_check_deals_buyer_router.callback_query(F.data == "check_deals_buyer")
async def check_deals_buyer(callback: CallbackQuery):
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(callback.from_user.id == Deals.buyer_id)
        )
        deals = deals.scalars().all()
        if deals:
            builder = InlineKeyboardBuilder()
            for deal in deals:
                builder.button(text=f"{deal.deal_id} {deal.march_model}",
                               callback_data=f"deal_list_buyer_{deal.deal_id}")
            builder.button(text="Вернуться в меню", callback_data="back_to_main_menu_buyer")
            builder.adjust(1)
            await callback.message.edit_text(text="Выберете сделку:",
                                             reply_markup=builder.as_markup())
        else:
            await callback.answer(text="У Вас пока что нет сделок!")


@callback_check_deals_buyer_router.callback_query(F.data.startswith("deal_list_buyer_"))
async def show_deal_list_buyer(callback: CallbackQuery):
    async with deals_session() as session:
        try:
            deal_id = callback.data.split("_")[-1]

            # Получаем сделку по ID
            result = await session.execute(
                select(Deals).where(deal_id == Deals.deal_id)
            )
            deal = result.scalar_one_or_none()

            if not deal:
                await callback.answer("Сделка не найдена", show_alert=True)
                return

            message_text = (
                f"Ваша Сделка №: {deal.deal_id}\n"
                f"Покупатель: {deal.buy_user}\n"
                f"Автомобиль: {deal.march_model}\n"
                f"VIN: {deal.vin_code}\n"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="❕ Инструкция по загрузке документов", callback_data="info_add_documents_buyer")
            builder.button(text="📥 Загрузка документов", callback_data="kb_menu_load_docs")
            builder.button(text="Регистрация на портале ЭПТС", url="https://dp.elpts.ru/#/auth/")
            builder.button(text="В главное меню", callback_data="back_to_main_menu_buyer")
            builder.adjust(1)

            await callback.message.delete()

            await callback.message.answer_photo(
                photo=deal.car_photo_id,
                caption=message_text,
                reply_markup=builder.as_markup(),
            )


        except Exception as e:
            logging.error(f"Error in show_deal_details: {e}")
            await callback.answer("Произошла ошибка", show_alert=True)


@callback_check_deals_buyer_router.callback_query(F.data == "back_to_main_menu_buyer")
async def back_to_main_menu_buyer(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(text=f"Добро пожаловать в панель Покупателя, благодарим Вас за выбор E-CarsBurg",
                         reply_markup=kb_buyer_main)