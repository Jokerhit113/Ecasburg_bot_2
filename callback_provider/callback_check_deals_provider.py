import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_provider_main

callback_check_deals_provider_router = Router()

@callback_check_deals_provider_router.callback_query(F.data == "check_deals_provider")
async def check_deals_provider(callback: CallbackQuery):
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(Deals.provider_id == callback.from_user.id)
        )
        deals = deals.scalars().all()
        if deals:
            builder = InlineKeyboardBuilder()
            for deal in deals:
                builder.button(text=f"{deal.deal_id} {deal.buy_user}",
                               callback_data=f"check_deal_{deal.deal_id}")
            builder.button(text="Вернуться в меню", callback_data="back_to_main_menu_provider")
            builder.adjust(1)
            await callback.message.edit_text(text="Выберете сделку:",
                                             reply_markup=builder.as_markup())
        else:
            await callback.answer(text="У Вас пока что нет сделок!")


@callback_check_deals_provider_router.callback_query(F.data.startswith("check_deal_"))
async def show_deal_details(callback: CallbackQuery, state: FSMContext):
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

            # Подтверждение выкупа автомобиля
            if not deal.buy_car_provider_photo_id and not deal.buy_car_provider_video_id:
                payment_btn = "⚠️"  # Нет ни фото, ни видео
            else:
                payment_btn = "✅"  # Есть хотя бы что-то из этого

            # Отчёт отправки авто до границы
            if not deal.provider_photo_car_before_border_id and not deal.provider_video_car_before_border_id:
                video_car_before_btn = "⚠️"  # Нет ни фото, ни видео
            else:
                video_car_before_btn = "✅"  # Есть хотя бы что-то из этого

            # Отчёт доставки авто на границу
            if not deal.provider_photo_car_border_id and not deal.provider_video_car_border_id:
                video_car_border_btn = "⚠️"  # Нет ни фото, ни видео
            else:
                video_car_border_btn = "✅"  # Есть хотя бы что-то из этого

            # Загрузить документы по автомобилю
            if not deal.document_docs_car_provider_id and not deal.photo_docs_car_provider_id:
                docs_car_provider_btn = "⚠️"  # Нет ни фото, ни видео
            else:
                docs_car_provider_btn = "✅"  # Есть хотя бы что-то из этого

            if not deal.car_go_to_rf_photo and not deal.car_go_to_rf_video:
                car_go_to_rf_btn = "⚠️"  # Нет ни фото, ни видео
            else:
                car_go_to_rf_btn = "✅"  # Есть хотя бы что-то из этого

            if payment_btn and video_car_before_btn and video_car_border_btn and docs_car_provider_btn == "✅":
                get_cmr_uin_btn = "✅"
            else:
                get_cmr_uin_btn = "⚠️"

            await state.update_data(payment_btn=payment_btn,
                                    video_car_before_btn = video_car_before_btn,
                                    video_car_border_btn = video_car_border_btn,
                                    docs_car_provider_btn = docs_car_provider_btn)


            # Формируем текст сообщения
            message_text = (
                f"Сделка №: {deal.deal_id}\n"
                f"Покупатель: {deal.buy_user}\n"
                f"Автомобиль: {deal.march_model}\n"
                f"VIN: {deal.vin_code}\n"
                f"Доп опции:\n {deal.additional_options}"
            )

            # Создаем клавиатуру для возврата
            builder = InlineKeyboardBuilder()
            builder.button(text=f"{payment_btn} Авто Выкуплен", callback_data=f"buy_car_provider")
            builder.button(text=f"{video_car_before_btn} Отправка авто до границы", callback_data=f"media_car_before_border")
            builder.button(text=f"{video_car_border_btn} Доставка авто на границу", callback_data=f"media_car_delivered_border")
            builder.button(text=f"{docs_car_provider_btn} Документы по автомобилю", callback_data=f"load_docs_car_provider")
            builder.button(text=f"{get_cmr_uin_btn} Запросить CMR и УИН у Брокера", callback_data=f"request_cmr_and_uin_from_the_broker")
            builder.button(text=f"{car_go_to_rf_btn} Передача авто в РФ", callback_data=f"car_go_to_rf")
            builder.button(text="Назад к списку", callback_data="back_check_deals_provider")
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

@callback_check_deals_provider_router.callback_query(F.data == "request_cmr_and_uin_from_the_broker")
async def request_crm_and_uin_from_the_broker(callback: CallbackQuery, bot: Bot, state: FSMContext):
    async with deals_session() as session:
        caption = callback.message.caption
        deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
                                )
        deal = deal.scalar_one_or_none()
        if not deal.broker_id:
            await callback.answer(text="Брокер сделки ещё не назначен", show_alert=True)
            return
        data = await state.get_data()
        payment_btn = data.get("payment_btn")
        video_car_before_btn = data.get("video_car_before_btn")
        video_car_border_btn = data.get("video_car_border_btn")
        docs_car_provider_btn = data.get("docs_car_provider_btn")
        if payment_btn and video_car_before_btn and video_car_border_btn and docs_car_provider_btn == "✅":

            message_text = (
                f"Сделка №: {deal.deal_id}\n"
                f"Покупатель: {deal.buy_user}\n"
                f"Автомобиль: {deal.march_model}\n"
                f"VIN: {deal.vin_code}\n"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="🔍 Проверить документы", callback_data="check_the_documents_for_the_car")
            await bot.send_photo(
                chat_id=deal.broker_id,
                photo=deal.car_photo_id,
                caption=f"{message_text}\n\n"
                        f"⚠️ Поставщик загрузил все документы и фото по автомобилю и Ожидает CMR и УИН",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
            await callback.message.answer("Запрос Брокеру на получение CMR и УИН Отправлен ✅")
        else:
            await callback.answer(
                text="Не все документы по автомобилю загружены",
                show_alert=True)
            return



@callback_check_deals_provider_router.callback_query(F.data == "back_check_deals_provider")
async def back_check_deals_provider(callback: CallbackQuery):
    await callback.message.delete()
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(Deals.provider_id == callback.from_user.id)
        )
        deals = deals.scalars().all()
        if deals:
            builder = InlineKeyboardBuilder()
            for deal in deals:
                builder.button(text=f"{deal.deal_id} {deal.buy_user}",
                               callback_data=f"check_deal_{deal.deal_id}")
            builder.button(text="Вернуться в меню", callback_data="back_to_main_menu_provider")
            builder.adjust(1)
            await callback.message.answer(text="Выберете сделку:",
                                             reply_markup=builder.as_markup())

@callback_check_deals_provider_router.callback_query(F.data == "back_to_main_menu_provider")
async def back_to_main_menu_provider(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(text="Welcome to the partner menu of E-CarsBurg.\n\n"
                                          "Use the button below to get a list of your deals.",
                                     reply_markup=kb_provider_main)