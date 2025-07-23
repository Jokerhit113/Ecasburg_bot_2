from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_check_status_buyer_router = Router()

@callback_check_status_buyer_router.callback_query(F.data == "check_status_buyer")
async def callback_check_status_buyer(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал: Проверить статус сделки")

    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Ваша Сделка №: ')[1])
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal.payment_confirmation_yes_no:
            car_payment_btn = "⚠️"
        else:
            car_payment_btn = "✅"

        if not deal.passport_photos and not deal.passport_documents and not deal.buyer_driver_license_photo and not deal.buyer_driver_license_photo and not deal.foreign_currency_account_statement_photo and not deal.foreign_currency_account_statement_docs and not deal.cash_flow_statement_photos and not deal.cash_flow_statement_docs and deal.snils_buyer_photos and not deal.snils_buyer_docs and not deal.buyer_phone_number and not deal.elpts_registration_photo:
            load_buyer_doc_btn = "⚠️"
        else:
            load_buyer_doc_btn = "✅"

        if deal.buy_car_provider_photo_id or deal.buy_car_provider_video_id:
            car_redemption_btn = f"✅ Доставка до Поставщика - {deal.delivery_time_car_to_provider} "
        elif car_payment_btn == "✅":
            car_redemption_btn = "⚠️"
        else:
            car_redemption_btn = "❕"

        if deal.provider_photo_car_before_border_id or deal.provider_video_car_before_border_id and deal.buy_car_provider_photo_id or deal.buy_car_provider_video_id:
            car_awersome_buy_btn = "✅"
        elif car_redemption_btn == "✅":
            car_awersome_buy_btn = "⚠️"

        else:
            car_awersome_buy_btn = "❕"

        if deal.provider_photo_car_before_border_id or deal.provider_video_car_before_border_id:
            car_go_to_border_btn = f"✅ Доставка до границы - {deal.delivery_time_car_to_border}"
        elif car_awersome_buy_btn == "✅":
            car_go_to_border_btn = "⚠️"
        else:
            car_go_to_border_btn = "❕"

        if deal.provider_photo_car_border_id or deal.provider_video_car_border_id:
            car_to_border_btn = f"✅"
        elif car_go_to_border_btn == "✅":
            car_to_border_btn = "⚠️"

        else:
            car_to_border_btn = "❕"

        if deal.document_doc_broker_id or deal.photo_docs_broker_id:
            car_from_border_btn = f"✅"
        elif car_to_border_btn == "✅":
            car_from_border_btn = "⚠️"
        else:
            car_from_border_btn = "❕"

        if deal.photo_car_get_border or deal.video_car_get_border:
            car_waiting_for_delivery_btn = f"✅"
        elif car_from_border_btn == "✅":
            car_waiting_for_delivery_btn = "⚠️"

        else:
            car_waiting_for_delivery_btn = "❕"

        if deal.photo_car_load_transportation or deal.video_car_load_transportation:
            car_delivery_for_rf_btn = f"✅"
        elif car_waiting_for_delivery_btn == "✅":
            car_delivery_for_rf_btn = "⚠️"
        else:
            car_delivery_for_rf_btn = "❕"

        # Формируем текст сообщения
        message_text = (
            f"ID: {deal.id}\n"
            f"Данные по сделке:\n\n"
            f"Сделка №: {deal.deal_id}\n"
            f"Покупатель: {deal.buy_user}\n"
            f"Автомобиль: {deal.march_model}\n"
            f"Vin code: {deal.vin_code}\n"


            f"Статус Заказа:\n"
            f"Оплата автомобиля {car_payment_btn}\n"
            f"Загрузка документов Покупателя {load_buyer_doc_btn}\n"
            f"Выкуп авто {car_redemption_btn}\n"
            f"Автомобиль у поставщика{car_awersome_buy_btn}\n"
            f"Автомобиль отправлен до границы {car_go_to_border_btn}\n"
            f"Автомобиль на пересечении границы {car_to_border_btn}\n"
            f"Таможенное оформление {car_from_border_btn}\n"
            f"Ожидание погрузки автомобиля на автовоз {car_waiting_for_delivery_btn}\n"
            f"Доставка по РФ {car_delivery_for_rf_btn}\n"
            f"Готов к выдаче\n\n"

            f"❕ - Ещё не начат\n"
            f"⚠️ - В процессе выполнения\n"
            f"✅ - Успешно завершен"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text=f"УДАЛИТЬ СООБЩЕНИЕ", callback_data=f"delete_message")
        builder.adjust(1)
        await callback.answer()
        await callback.message.answer(message_text, reply_markup=builder.as_markup())
