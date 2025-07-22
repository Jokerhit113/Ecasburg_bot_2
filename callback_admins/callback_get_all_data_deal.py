import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from typing import List, Union

from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals

callback_get_all_data_deal_router = Router()

async def get_all_data_deal(
        bot: Bot,
        chat_id: int,
        media_items: Union[List[str], str, None],
        caption: str,
        media_type: str = "photo"
) -> None:
    """Отправляет медиафайлы частями по 10 штук с обработкой ошибок"""
    if not media_items:
        return

    # Нормализуем входные данные в список
    if isinstance(media_items, str):
        media_items = [media_items]
    elif not isinstance(media_items, list):
        logging.error(f"Invalid media_items type: {type(media_items)}")
        return

    # Фильтруем невалидные file_id
    valid_media = [m for m in media_items if m and isinstance(m, str) and len(m) > 20]

    if not valid_media:
        logging.warning("No valid media items found")
        return

    # Разбиваем на группы по 10 элементов
    chunk_size = 10
    for i in range(0, len(valid_media), chunk_size):
        chunk = valid_media[i:i + chunk_size]
        try:
            media_group = MediaGroupBuilder(caption=caption if i == 0 else "")

            for media_id in chunk:
                if media_type == "photo":
                    media_group.add_photo(media=media_id)
                elif media_type == "document":
                    media_group.add_document(media=media_id)
                elif media_type == "video":
                    media_group.add_video(media=media_id)

            await bot.send_media_group(chat_id=chat_id, media=media_group.build())
        except Exception as e:
            logging.error(f"Error sending media chunk {i}-{i + chunk_size}: {e}")


@callback_get_all_data_deal_router.callback_query(F.data == "contract_1")
async def callback_contract_1(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.contract_photo_id,
            deal.contract_docs_id,

        ])

        if not has_documents:
            await callback.answer("Документы ещё не загружены")

        if deal.contract_photo_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.contract_photo_id,
                caption="Фотографии Договора:",
                media_type="photo"
            )
        if deal.contract_docs_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.contract_docs_id,
                caption="Сканы Договора:",
                media_type="document"
            )


        await callback.answer("Договор Получен")


@callback_get_all_data_deal_router.callback_query(F.data == "payment_proof_2")
async def payment_proof_2(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return
        has_documents = any([
            deal.payment_photo_id,
            deal.payment_document_id,
        ])

        if not has_documents:
            await callback.answer("Документы ещё не загружены")

        if deal.payment_photo_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.payment_photo_id,
                caption="Фотографии Квитанции об оплате автомобиля покупателем:",
                media_type="photo"
            )
        if deal.payment_document_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.payment_document_id,
                caption="Сканы Квитанции об оплате автомобиля покупателем:",
                media_type="document"
            )

        await callback.answer("Квитанция об оплате автомобиля покупателем Получена")


@callback_get_all_data_deal_router.callback_query(F.data == "get_docs_buyer_docs_3")
async def get_docs_buyer_docs_3(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.buyer_phone_number,
            deal.passport_photos,
            deal.passport_documents,
            deal.inn_photo,
            deal.inn_docs,
            deal.buyer_driver_license_photo,
            deal.buyer_driver_license_docs,
            deal.foreign_currency_account_statement_photo,
            deal.foreign_currency_account_statement_docs,
            deal.cash_flow_statement_photos,
            deal.cash_flow_statement_docs,
            deal.snils_buyer_photos,
            deal.snils_buyer_docs,
            deal.elpts_registration_photo,
            deal.payment_document_invoice_to_buyer

        ])

        if not has_documents:
            await callback.answer("Документы ещё не загружены")

        if deal.buyer_phone_number:
            await callback.message.answer(
                text="Анкета Покупателя:\n\n"
                     f"Заказчик: {deal.buy_user}\n"
                     f"Номер телефона: {deal.buyer_phone_number}\n"
                     f"Фактический адрес проживания: {deal.buyer_actual_address_of_residence}\n"
                     f"E-mail: {deal.buyer_email_address}\n"
                     f"Был ли ввоз автомобиля из-за границы за последние 3 года: {deal.buyer_imported_yes_no}\n"
                     f"Есть ли автомобиль в пользовании в данный момент: {deal.buyer_have_car}\n"
            )

        if deal.passport_photos:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.passport_photos,
                caption="Фото Паспорта:",
                media_type="photo"
            )
        if deal.passport_documents:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.passport_documents,
                caption="Сканы Паспорта:",
                media_type="document"
            )
        if deal.inn_photo:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.inn_photo,
                caption="Фото ИНН:",
                media_type="photo"
            )
        if deal.inn_docs:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.inn_docs,
                caption="Скан ИНН:",
                media_type="document"
            )

        if deal.buyer_driver_license_photo:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.buyer_driver_license_photo,
                caption="Фото Водительского Удостоверения:",
                media_type="photo"
            )
        if deal.buyer_driver_license_docs:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.buyer_driver_license_docs,
                caption="Сканы Водительского Удостоверения:",
                media_type="document"
            )
        if deal.foreign_currency_account_statement_photo:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.foreign_currency_account_statement_photo,
                caption="Фото Выписки по валютному счёту:",
                media_type="photo"
            )
        if deal.foreign_currency_account_statement_docs:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.foreign_currency_account_statement_docs,
                caption="Сканы Выписки по валютному счёту:",
                media_type="document"
            )
        if deal.cash_flow_statement_photos:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.cash_flow_statement_photos,
                caption="Фото Справки движения денег по валютному счёту:",
                media_type="photo"
            )
        if deal.cash_flow_statement_docs:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.cash_flow_statement_docs,
                caption="Сканы Справки движения денег по валютному счёту:",
                media_type="document"
            )
        if deal.snils_buyer_photos:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.snils_buyer_photos,
                caption="Фото СНИЛС:",
                media_type="photo"
            )
        if deal.snils_buyer_docs:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.snils_buyer_docs,
                caption="Скан СНИЛС:",
                media_type="document"
            )

        if deal.elpts_registration_photo:
            await callback.message.answer_photo(
                photo=deal.elpts_registration_photo,
                caption="Фото регистрации в ЭПТС:",
            )
        if deal.payment_document_invoice_to_buyer:
            await callback.message.answer_document(
                document=deal.payment_document_invoice_to_buyer,
                caption="Квитанция подтверждения оплаты счёта от Брокера:",
            )

        await callback.answer("Все загруженные документы Покупателя Получены")


@callback_get_all_data_deal_router.callback_query(F.data == "car_purchase_4")
async def car_purchase_4(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.buy_car_provider_photo_id,
            deal.buy_car_provider_video_id,

        ])

        if not has_documents:
            await callback.answer("Фото / Видео ещё не загружены")

        if deal.buy_car_provider_photo_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.buy_car_provider_photo_id,
                caption="Фото выкупа автомобиля поставщиком:",
                media_type="photo"
            )
        if deal.buy_car_provider_video_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.buy_car_provider_video_id,
                caption="Видео выкупа автомобиля поставщиком:",
                media_type="video"
            )

        await callback.answer("Фото/Видео выкупа автомобиля поставщиком Получены")

@callback_get_all_data_deal_router.callback_query(F.data == "pre_border_5")
async def pre_border_5(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.provider_photo_car_before_border_id,
            deal.provider_video_car_before_border_id,

        ])

        if not has_documents:
            await callback.answer("Фото / Видео ещё не загружены")

        if deal.provider_photo_car_before_border_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.provider_photo_car_before_border_id,
                caption="Фото автомобиля до отправки на границу от поставщика:",
                media_type="photo"
            )
        if deal.provider_video_car_before_border_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.provider_video_car_before_border_id,
                caption="Видео автомобиля до отправки на границу от поставщика:",
                media_type="video"
            )

        await callback.answer("Фото/Видео автомобиля до отправки на границу от поставщика Получены")

@callback_get_all_data_deal_router.callback_query(F.data == "at_border_6")
async def at_border_6(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.provider_photo_car_border_id,
            deal.provider_video_car_border_id,

        ])

        if not has_documents:
            await callback.answer("Фото / Видео ещё не загружены")

        if deal.provider_photo_car_border_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.provider_photo_car_border_id,
                caption="Фото автомобиля на границе от поставщика:",
                media_type="photo"
            )
        if deal.provider_video_car_border_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.provider_video_car_border_id,
                caption="Видео автомобиля на границе от поставщика:",
                media_type="video"
            )

        await callback.answer("Фото/Видео автомобиля на границе от поставщика Получены")


@callback_get_all_data_deal_router.callback_query(F.data == "supplier_docs_7")
async def supplier_docs_7(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.document_docs_car_provider_id,
            deal.photo_docs_car_provider_id,

        ])

        if not has_documents:
            await callback.answer("Документы ещё не загружены")

        if deal.document_docs_car_provider_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.document_docs_car_provider_id,
                caption="Сканы документов по автомобилю от поставщика:",
                media_type="document"
            )
        if deal.photo_docs_car_provider_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.photo_docs_car_provider_id,
                caption="Фото документов по автомобилю от поставщика:",
                media_type="photo"
            )

        await callback.answer("Документы по автомобилю от поставщика Получены")

@callback_get_all_data_deal_router.callback_query(F.data == "get_docs_broker_docs_8")
async def get_docs_broker_docs_8(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return
        has_documents = any([
            deal.document_doc_broker_id,
            deal.photo_docs_broker_id,
        ])

        if not has_documents:
            await callback.answer("Документы ещё не загружены")

        if deal.photo_docs_broker_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.photo_docs_broker_id,
                caption="Фотографии по автомобилю от Брокера:",
                media_type="photo"
            )
        if deal.document_doc_broker_id:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.document_doc_broker_id,
                caption="Сканы по автомобилю от Брокера:",
                media_type="document"
            )

        if deal.payment_invoice_to_buyer:
            await callback.message.answer_document(
                document=deal.payment_invoice_to_buyer,
                caption="Квитанция на оплату Таможни от Брокера"
            )

        if deal.payment_invoice_to_buyer_text:
            await callback.message.answer(f"Брокер отправил Покупателю для оплаты Таможни следующие Реквизиты:\n\n"
                                          f"{deal.payment_invoice_to_buyer_text}\n")

        await callback.answer("Документы от Брокера Получены")

@callback_get_all_data_deal_router.callback_query(F.data == "transfer_rf_9")
async def transfer_rf_9(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.car_go_to_rf_photo,
            deal.car_go_to_rf_video,

        ])

        if not has_documents:
            await callback.answer("Фото / Видео ещё не загружены")

        if deal.car_go_to_rf_photo:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.car_go_to_rf_photo,
                caption="Фото передачи авто в РФ:",
                media_type="photo"
            )
        if deal.car_go_to_rf_video:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.car_go_to_rf_video,
                caption="Видео передачи авто в РФ:",
                media_type="video"
            )

        await callback.answer("Фото/Видео передачи авто в РФ Получены")

@callback_get_all_data_deal_router.callback_query(F.data == "border_receive_10")
async def border_receive_10(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.photo_car_get_border,
            deal.video_car_get_border,

        ])

        if not has_documents:
            await callback.answer("Фото / Видео ещё не загружены")

        if deal.photo_car_get_border:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.photo_car_get_border,
                caption="Фото Получения Авто на границе:",
                media_type="photo"
            )
        if deal.video_car_get_border:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.video_car_get_border,
                caption="Видео Получения Авто на границе:",
                media_type="video"
            )

        await callback.answer("Фото/Видео Получения Авто на границе Получены")

@callback_get_all_data_deal_router.callback_query(F.data == "loading_transport_11")
async def loading_transport_11(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.photo_car_load_transportation,
            deal.video_car_load_transportation,

        ])

        if not has_documents:
            await callback.answer("Фото / Видео ещё не загружены")

        if deal.photo_car_load_transportation:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.photo_car_load_transportation,
                caption="Фото Погруженного Автомобиля на Воз:",
                media_type="photo"
            )
        if deal.video_car_load_transportation:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.video_car_load_transportation,
                caption="Видео Погруженного Автомобиля на Воз:",
                media_type="video"
            )

        await callback.answer("Фото/Видео Погруженного Автомобиля на Воз Получены")

@callback_get_all_data_deal_router.callback_query(F.data == "get_docs_carrier_docs_12")
async def get_docs_carrier_docs_12(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        has_documents = any([
            deal.photo_docs_car_carrier,
            deal.docs_docs_car_carrier,

        ])

        if not has_documents:
            await callback.answer("Фото / Сканы ещё не загружены")

        if deal.photo_docs_car_carrier:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.photo_docs_car_carrier,
                caption="Фото Документов по автомобилю от Перевозчика:",
                media_type="photo"
            )
        if deal.docs_docs_car_carrier:
            await get_all_data_deal(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                media_items=deal.docs_docs_car_carrier,
                caption="Сканы Документов по автомобилю от Перевозчика:",
                media_type="document"
            )

        await callback.answer("Фото/Сканы Документов по автомобилю от Перевозчика Получены")