import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_broker_main

callback_check_deals_broker_router = Router()

@callback_check_deals_broker_router.callback_query(F.data == "check_deals_broker")
async def check_deals_broker(callback: CallbackQuery):
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(Deals.broker_id == callback.from_user.id)
        )
        deals = deals.scalars().all()
        if deals:
            builder = InlineKeyboardBuilder()
            for deal in deals:
                builder.button(text=f"{deal.deal_id} {deal.buy_user}",
                               callback_data=f"list_broker_check_deal_{deal.deal_id}")
            builder.button(text="Вернуться в меню", callback_data="back_to_main_menu_broker")
            builder.adjust(1)

            await callback.message.edit_text(text="Выберете сделку:",
                                             reply_markup=builder.as_markup())
        else:
            await callback.answer(text="У Вас пока что нет сделок!")


@callback_check_deals_broker_router.callback_query(F.data.startswith("list_broker_check_deal_"))
async def show_deal_broker_list(callback: CallbackQuery):
    async with deals_session() as session:
        try:
            deal_id = callback.data.split("_")[-1]

            result = await session.execute(
                select(Deals).where(Deals.deal_id == deal_id)
            )
            deal = result.scalar_one_or_none()
            if not deal:
                await callback.answer(text="Сделка не найдена")
                return
            message_text = (
                f"Сделка №: {deal.deal_id}\n"
                f"Покупатель: {deal.buy_user}\n"
                f"Автомобиль: {deal.march_model}\n"
                f"VIN: {deal.vin_code}\n"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text=f"Проверить документы по авто",
                           callback_data=f"сheck_the_documents_for_the_car")
            builder.button(text=f"Проверить документы покупателя",
                           callback_data=f"check_the_buyer_documents")
            builder.button(text=f"Загрузить документы",
                           callback_data=f"load_docs_broker")
            builder.button(text=f"Завершить работу по сделке",
                           callback_data=f"end_deal_broker")
            builder.button(text="Назад к списку", callback_data="back_to_main_menu_broker")
            builder.adjust(1)
            await callback.message.delete()

            await callback.message.answer_photo(
                photo=deal.car_photo_id,
                caption=message_text,
                reply_markup=builder.as_markup()
            )
        except Exception as e:
            logging.error(f"Error in broker_check_deal_: {e}")
            await callback.answer("Произошла ошибка", show_alert=True)




@callback_check_deals_broker_router.callback_query(F.data == "back_to_main_menu_broker")
async def back_to_main_menu_broker(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(text="Добро пожаловать в меню Брокера E-CarsBurg.\n\n"
                                          "Воспользуйтесь кнопкой ниже для получения списка Ваших сделок.",
                                     reply_markup=kb_broker_main)