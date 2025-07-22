import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User

callback_status_deal_router = Router()


@callback_status_deal_router.callback_query(F.data == "check_status")
async def callback_get_deals_check_status(callback: CallbackQuery):
    try:
        # Получаем ID сделки из сообщения
        caption = callback.message.caption or ""
        deal_id = caption.split('\n')[0].split('ID: ')[1]

        async with deals_session() as session:
            # Получаем сделку
            deal = await session.get(Deals, deal_id)
            if not deal:
                await callback.answer("Сделка не найдена", show_alert=True)
                return

            async with user_session() as session_user:
                # Получаем всех участников сделки одним запросом
                user_ids = [
                    deal.buyer_id,
                    deal.provider_id,
                    deal.broker_id,
                    deal.carrier_id
                ]

                users = await session_user.execute(
                    select(User).where(User.user_id.in_(user_ids))
                )
                users = {user.user_id: user for user in users.scalars()}

                # Создаем клавиатуру
                builder = InlineKeyboardBuilder()
                buttons = [
                    ("Договор по сделке", "1"),
                    ("Чек об оплате покупателем", "2"),
                    ("Документы Покупателя", "3"),
                    ("Выкупа Автомобиля", "4"),
                    ("Авто до отправки на границу", "5"),
                    ("Авто на Границе", "6"),
                    ("Документы по авто от Поставщика", "7"),
                    ("Документы от Брокера", "8"),
                    ("Получение авто на границе", "9"),
                    ("Передача авто в РФ", "10"),
                    ("Погрузка авто на Воз", "11"),
                    ("Документы от Перевозчика", "12"),
                    ("Назад к Списку", f"deal_detail_{deal.id}")
                ]

                for text, callback_data in buttons:
                    builder.button(text=text, callback_data=callback_data)

                builder.adjust(1)  # Все кнопки в отдельных рядах

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
                caption_text = (
                    f"ID: {deal.id}\n"
                    f"Данные по сделке:\n\n"
                    f"Сделка №: {deal.deal_id}\n"
                    f"Покупатель: {users.get(deal.buyer_id, User(name='Не указан')).name}\n"
                    f"Автомобиль: {deal.march_model}\n"
                    f"Vin code: {deal.vin_code}\n"
                    f"Поставщик: {users.get(deal.provider_id, User(name='Не указан')).name}\n"
                    f"Брокер: {users.get(deal.broker_id, User(name='Не указан')).name}\n"
                    f"Перевозчик: {users.get(deal.carrier_id, User(name='Не указан')).name}\n\n"
                    f"Статус оплаты покупателя: {deal.payment_confirmation_yes_no}\n"
                    f"Статус проверки документов покупателя: {deal.confirmation_of_acceptance_of_documents_from_buyer}\n"
                    f"Статус проверки документов поставщика: {deal.confirmation_of_acceptance_of_documents_from_suppliers}\n"
                    f"Статус оплаты счёта Покупателем от Брокера: {deal.payment_document_invoice_to_buyer_yes_no}\n\n"
                    
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

                await callback.message.edit_caption(
                    caption=caption_text,
                    reply_markup=builder.as_markup()
                )

    except IndexError:
        await callback.answer("Ошибка: неверный формат сообщения", show_alert=True)
    except Exception as e:
        logging.error(f"Error in check_status: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обработке запроса", show_alert=True)


