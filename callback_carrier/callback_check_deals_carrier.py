import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_carrier_main

callback_check_deals_carrier_router = Router()

@callback_check_deals_carrier_router.callback_query(F.data == "check_deals_carrier")
async def check_deals_carrier(callback: CallbackQuery):
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(Deals.carrier_id == callback.from_user.id)
        )
        deals = deals.scalars().all()
        if deals:
            builder = InlineKeyboardBuilder()
            for deal in deals:
                builder.button(text=f"{deal.deal_id} {deal.buy_user}",
                               callback_data=f"deal_list_carrier_{deal.deal_id}")
            builder.button(text="Вернуться в меню", callback_data="back_to_main_menu_carrier")
            builder.adjust(1)
            await callback.message.edit_text(text="Выберете сделку:",
                                             reply_markup=builder.as_markup())
        else:
            await callback.answer(text="У Вас пока что нет сделок!")

@callback_check_deals_carrier_router.callback_query(F.data.startswith("deal_list_carrier_"))
async def show_deal_details(callback: CallbackQuery):
    """Показывает детали конкретной сделки"""
    async with deals_session() as session:
        try:
            deal_id = callback.data.split("_")[-1]

            # Получаем сделку по ID
            result = await session.execute(
                select(Deals).where(Deals.deal_id == deal_id)
            )
            deal = result.scalar_one_or_none()

            if not deal:
                await callback.answer("Сделка не найдена", show_alert=True)
                return
            # Формируем текст сообщения
            message_text = (
                f"Сделка №: {deal.deal_id}\n"
                f"Покупатель: {deal.buy_user}\n"
                f"Автомобиль: {deal.march_model}\n"
                f"VIN: {deal.vin_code}\n"
            )

            if not deal.photo_car_get_border and not deal.video_car_get_border:
                report_of_receiving_a_car_at_the_border_btn = "⚠️"  # Нет ни фото, ни видео
            else:
                report_of_receiving_a_car_at_the_border_btn = "✅"  # Есть хотя бы что-то из этого

            if not deal.photo_car_load_transportation and not deal.video_car_load_transportation:
                report_of_loading_a_vehicle_for_transportation_btn = "⚠️"  # Нет ни фото, ни видео
            else:
                report_of_loading_a_vehicle_for_transportation_btn = "✅"  # Есть хотя бы что-то из этого

            if not deal.photo_docs_car_carrier and not deal.docs_docs_car_carrier:
                load_docs_carrier_btn = "⚠️"  # Нет ни фото, ни видео
            else:
                load_docs_carrier_btn = "✅"  # Есть хотя бы что-то из этого

            # Создаем клавиатуру для возврата
            builder = InlineKeyboardBuilder()
            builder.button(text=f"{report_of_receiving_a_car_at_the_border_btn} Отчёт получения Авто на границе", callback_data=f"report_of_receiving_a_car_at_the_border")
            builder.button(text=f"{report_of_loading_a_vehicle_for_transportation_btn} Отчёт погрузки автомобиля", callback_data=f"report_of_loading_a_vehicle_for_transportation")
            builder.button(text=f"{load_docs_carrier_btn} Документы по перевозке автомобиля", callback_data=f"load_docs_carrier")

            builder.button(text="Назад к списку", callback_data="back_check_deals_carrier")
            builder.adjust(1)
            await callback.message.delete()

            await callback.message.answer_photo(
                photo=deal.car_photo_id,
                caption=message_text,
                reply_markup=builder.as_markup()
            )

        except Exception as e:
            logging.error(f"Error in show_deal_details: {e}")
            await callback.answer("Произошла ошибка", show_alert=True)

@callback_check_deals_carrier_router.callback_query(F.data == "back_check_deals_carrier")
async def back_check_deals_carrier(callback: CallbackQuery):
    await callback.message.delete()
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(Deals.carrier_id == callback.from_user.id)
        )
        deals = deals.scalars().all()
        if deals:
            builder = InlineKeyboardBuilder()
            for deal in deals:
                builder.button(text=f"{deal.deal_id} {deal.buy_user}",
                               callback_data=f"deal_list_carrier_{deal.deal_id}")
            builder.button(text="Вернуться в меню", callback_data="back_to_main_menu_carrier")
            builder.adjust(1)
            await callback.message.answer(text="Выберете сделку:",
                                             reply_markup=builder.as_markup())


@callback_check_deals_carrier_router.callback_query(F.data == "back_to_main_menu_carrier")
async def back_to_main_menu_carrier(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(text="Добро пожаловать в меню Перевозчика автомобилей компании E-CarsBurg.\n\n"
                                          "Воспользуйтесь кнопкой ниже для получения списка Ваших сделок.",
                                     reply_markup=kb_carrier_main)