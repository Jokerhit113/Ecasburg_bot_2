import logging
from typing import List, Union

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select

from core.state_fsm import Broker
from data_base.db_deals import deals_session, Deals

callback_check_the_buyer_documents_router = Router()


async def send_media_chunks(
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

            await bot.send_media_group(chat_id=chat_id, media=media_group.build())
        except Exception as e:
            logging.error(f"Error sending media chunk {i}-{i + chunk_size}: {e}")


@callback_check_the_buyer_documents_router.callback_query(F.data == "check_the_buyer_documents")
async def check_the_documents_for_the_car_router(callback: CallbackQuery):
    try:
        caption = callback.message.caption
        deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
        async with deals_session() as session:
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Принять Документы", callback_data="accept_the_documents_buyer")
            builder.button(text="❌ Отклонить Документы", callback_data="reject_the_documents_buyer")
            builder.adjust(1)

            deals = await session.execute(select(Deals).where(Deals.deal_id == deal_id))
            deals = deals.scalar_one_or_none()

            if not deals:
                await callback.answer("Сделка не найдена", show_alert=True)
                return

            # Проверка наличия документов
            has_documents = any([
                deals.passport_photos,
                deals.passport_documents,
                deals.foreign_currency_account_statement_photo,
                deals.foreign_currency_account_statement_docs,
                deals.cash_flow_statement_photos,
                deals.cash_flow_statement_docs,
                deals.snils_buyer_photos,
                deals.snils_buyer_docs,
                deals.buyer_phone_number,
                deals.elpts_registration_photo
            ])

            if not has_documents:
                await callback.answer("Документы ещё не загружены Поставщиком", show_alert=True)
                return

            # Анкета покупателя
            if deals.buyer_phone_number:
                await callback.message.answer(
                    text="Анкета Покупателя:\n\n"
                         f"Заказчик: {deals.buy_user}\n"
                         f"Номер телефона: {deals.buyer_phone_number}\n"
                         f"Фактический адрес проживания: {deals.buyer_actual_address_of_residence}\n"
                         f"E-mail: {deals.buyer_email_address}\n"
                         f"Был ли ввоз автомобиля из-за границы за последние 3 года: {deals.buyer_imported_yes_no}\n"
                         f"Есть ли автомобиль в пользовании в данный момент: {deals.buyer_have_car}\n"
                )


            # Квитанция об оплате автомобиля
            if deals.payment_photo_id:
                await callback.message.answer_photo(photo=deals.payment_photo_id,
                                                    caption="Фото Квитанции об оплате автомобиля")

            if deals.payment_document_id:
                await callback.message.answer_document(document=deals.payment_document_id,
                                                       caption="Скан Квитанции об оплате автомобиля")

            # ПАСПОРТ
            if deals.passport_photos:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.passport_photos,
                    caption="Фото ПАСПОРТА:",
                    media_type="photo"
                )

            if deals.passport_documents:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.passport_documents,
                    caption="Сканы ПАСПОРТА:",
                    media_type="document"
                )

            # ИНН
            if deals.inn_photo:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.inn_photo,
                    caption="Фото ИНН:",
                    media_type="photo"
                )

            if deals.inn_docs:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.inn_docs,
                    caption="Скан ИНН:",
                    media_type="document"
                )

            # Водительское удостоверение
            if deals.buyer_driver_license_photo:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.buyer_driver_license_photo,
                    caption="Фото Водительского Удостоверения:",
                    media_type="photo"
                )

            if deals.buyer_driver_license_docs:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.buyer_driver_license_docs,
                    caption="Сканы Водительского Удостоверения:",
                    media_type="document"
                )

            # Выписки по счетам
            if deals.foreign_currency_account_statement_photo:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.foreign_currency_account_statement_photo,
                    caption="Фото Выписки по валютному счёту:",
                    media_type="photo"
                )

            if deals.foreign_currency_account_statement_docs:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.foreign_currency_account_statement_docs,
                    caption="Сканы Выписки по валютному счёту:",
                    media_type="document"
                )

            # Движения денежных средств
            if deals.cash_flow_statement_photos:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.cash_flow_statement_photos,
                    caption="Фото Справки движения денег по валютному счёту:",
                    media_type="photo"
                )

            if deals.cash_flow_statement_docs:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.cash_flow_statement_docs,
                    caption="Сканы Справки движения денег по валютному счёту:",
                    media_type="document"
                )

            # СНИЛС
            if deals.snils_buyer_photos:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.snils_buyer_photos,
                    caption="Фото СНИЛС:",
                    media_type="photo"
                )

            if deals.snils_buyer_docs:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.snils_buyer_docs,
                    caption="Сканы СНИЛС:",
                    media_type="document"
                )

            # ЭПТС
            if deals.elpts_registration_photo:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.elpts_registration_photo,
                    caption="Фото регистрации в ЭПТС:",
                    media_type="photo"
                )

            # Итоговое сообщение с кнопками
            message_text = (
                f"Сделка №: {deals.deal_id}\n"
                f"Покупатель: {deals.buy_user}\n"
                f"Автомобиль: {deals.march_model}\n"
                f"VIN: {deals.vin_code}\n"
            )

            if not deals.confirmation_of_acceptance_of_documents_from_buyer:
                await callback.message.answer(
                    text=message_text,
                    reply_markup=builder.as_markup()
                )

            await callback.answer()

    except Exception as e:
        logging.error(f"Error in check_the_documents_for_the_car: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обработке документов", show_alert=True)


# ... остальные обработчики остаются без изменений ...

@callback_check_the_buyer_documents_router.callback_query(F.data == "accept_the_documents_buyer")
async def accept_the_documents_buyer(callback: CallbackQuery, bot: Bot):
    async with deals_session() as session:
        text = callback.message.text
        deal_id = int(text.split('\n')[0].split('Сделка №: ')[1])
        deals = await session.execute(
            select(Deals).where(deal_id == Deals.deal_id)
        )
        deals = deals.scalar_one_or_none()

        deals.confirmation_of_acceptance_of_documents_from_buyer = "Документы приняты"

        await session.commit()
        message_text = (
            f"Сделка №: {deals.deal_id}\n"
            f"Покупатель: {deals.buy_user}\n"
            f"Автомобиль: {deals.march_model}\n"
            f"VIN: {deals.vin_code}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад в Меню", callback_data=f"list_broker_check_deal_{deal_id}")
        builder.adjust(1)
        await bot.send_message(
            chat_id=deals.buyer_id,
            text=f"{message_text}\n\n"
                 f"Документы приняты Брокером ✅",
        )
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Документы Приняты ✅",
            reply_markup=builder.as_markup()
        )

@callback_check_the_buyer_documents_router.callback_query(F.data == "reject_the_documents_buyer")
async def reject_the_documents_buyer(callback: CallbackQuery, state: FSMContext):
    async with deals_session() as session:
        text = callback.message.text
        deal_id = int(text.split('\n')[0].split('Сделка №: ')[1])
        deals = await session.execute(
            select(Deals).where(deal_id == Deals.deal_id)
        )
        deals = deals.scalar_one_or_none()

        deals.confirmation_of_acceptance_of_documents_from_buyer = ""

        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Документы не приняты ❌",
            reply_markup=None
        )
        await callback.message.answer(
            text="Напишите ОДНИМ СООБЩЕНИЕМ, что нужно исправить для принятия документов:"
        )
        await state.update_data(deal_id=deals.deal_id)
        await state.set_state(Broker.waiting_for_reason_buyer)

@callback_check_the_buyer_documents_router.message(Broker.waiting_for_reason_buyer)
async def waiting_for_reason_buyer(message: Message, state: FSMContext):

    await state.update_data(reason=message.text)

    builder = InlineKeyboardBuilder()
    builder.button(text="Верно ✅", callback_data="accept_the_reason_buyer")
    builder.button(text="Написать заново ❌", callback_data="reject_the_reason_buyer")

    await message.answer(
        text=f"Вы указали причину отказа принятия документов:\n\n"
             f"{message.text}\n\n"
             f"Верно?",
        reply_markup=builder.as_markup()
    )

@callback_check_the_buyer_documents_router.callback_query(F.data == "accept_the_reason_buyer")
async def accept_the_reason_buyer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    deal_id = data["deal_id"]
    reason = data["reason"]
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(deal_id == Deals.deal_id)
        )
        deals = deals.scalar_one_or_none()
        message_text = (
            f"Сделка №: {deals.deal_id}\n"
            f"Покупатель: {deals.buy_user}\n"
            f"Автомобиль: {deals.march_model}\n"
            f"VIN: {deals.vin_code}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="Исправлено ✅", callback_data="fixed_it_document_buyer")
        await bot.send_photo(
            chat_id=deals.buyer_id,
            photo=deals.car_photo_id,
            caption=f"{message_text}\n\n"
                    f"⚠️ВАШИ ДОКУМЕНТЫ НЕ ПРИНЯТЫ ❌ БРОКЕРОМ ⚠️\n\n"
                    f"{reason}\n\n"
                    f"Исправьте все прописанные Брокером исправления и нажмите кнопку ниже Исправлено ✅",
            reply_markup=builder.as_markup()
        )
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Покупатель получил уведомление с пояснениями.",
            reply_markup=None
        )
        await state.clear()


@callback_check_the_buyer_documents_router.callback_query(F.data == "fixed_it_document_buyer")
async def fixed_it_document_buyer(callback: CallbackQuery, bot: Bot):
    async with deals_session() as session:
        text = callback.message.caption
        deal_id = int(text.split('\n')[0].split('Сделка №: ')[1])
        deals = await session.execute(
            select(Deals).where(deal_id == Deals.deal_id)
        )
        deals = deals.scalar_one_or_none()
        message_text = (
            f"Сделка №: {deals.deal_id}\n"
            f"Покупатель: {deals.buy_user}\n"
            f"Автомобиль: {deals.march_model}\n"
            f"VIN: {deals.vin_code}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 Проверить документы", callback_data="check_the_buyer_documents")
        await bot.send_photo(
            chat_id=deals.broker_id,
            photo=deals.car_photo_id,
            caption=f"{message_text}\n\n"
                    f"Покупатель исправил недочёты ✅\n"
                    f"Пожалуйста проверьте документы снова",
            reply_markup=builder.as_markup()
        )
        await callback.message.edit_reply_markup()
        await callback.message.answer(text=f"{message_text}\n\n"
                                              f"Брокер получил уведомление об исправлении документов ✅")

@callback_check_the_buyer_documents_router.callback_query(F.data == "reject_the_reason_provider")
async def reject_the_reason_buyer(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        text="Напишите ОДНИМ СООБЩЕНИЕМ, что нужно исправить для принятия документов:"
    )