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

callback_check_the_documents_for_the_car_router = Router()


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
                elif media_type == "video":
                    media_group.add_video(media=media_id)

            await bot.send_media_group(chat_id=chat_id, media=media_group.build())
        except Exception as e:
            logging.error(f"Error sending media chunk {i}-{i + chunk_size}: {e}")


@callback_check_the_documents_for_the_car_router.callback_query(F.data == "check_the_documents_for_the_car")
async def check_the_documents_for_the_car_router(callback: CallbackQuery):
    try:
        caption = callback.message.caption
        deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
        async with deals_session() as session:
            builder = InlineKeyboardBuilder()
            builder.button(text="✅ Принять Документы", callback_data="accept_the_documents_car_provider")
            builder.button(text="❌ Отклонить Документы", callback_data="reject_the_documents_car_provider")
            builder.adjust(1)

            deals = await session.execute(
                select(Deals).where(Deals.deal_id == deal_id)
            )
            deals = deals.scalar_one_or_none()

            if not deals:
                await callback.answer("Сделка не найдена", show_alert=True)
                return

            # Проверка наличия документов
            if not deals.photo_docs_car_provider_id and not deals.document_docs_car_provider_id:
                await callback.answer("Документы ещё не загружены Поставщиком", show_alert=True)
                return

            # Отправка фото документов с разбивкой на группы
            if deals.photo_docs_car_provider_id:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.photo_docs_car_provider_id,
                    caption="Фото документов:",
                    media_type="photo"
                )

            # Отправка сканов документов с разбивкой на группы
            if deals.document_docs_car_provider_id:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.document_docs_car_provider_id,
                    caption="Сканы документов:",
                    media_type="document"
                )

            # Отправка фото автомобиля на границе
            if deals.provider_photo_car_border_id:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.provider_photo_car_border_id,
                    caption="Фото автомобиля на границе:",
                    media_type="photo"
                )
            # Отправка Видео автомобиля на границе
            if deals.provider_video_car_border_id:
                await send_media_chunks(
                    bot=callback.bot,
                    chat_id=callback.message.chat.id,
                    media_items=deals.provider_video_car_border_id,
                    caption="Видео автомобиля на границе:",
                    media_type="video"
                )

            message_text = (
                f"Сделка №: {deals.deal_id}\n"
                f"Покупатель: {deals.buy_user}\n"
                f"Автомобиль: {deals.march_model}\n"
                f"VIN: {deals.vin_code}\n"
            )

            if not deals.confirmation_of_acceptance_of_documents_from_suppliers:
                await callback.message.answer(
                    text=message_text,
                    reply_markup=builder.as_markup()
                )

            await callback.answer()

    except Exception as e:
        logging.error(f"Error in check_the_documents_for_the_car: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обработке документов", show_alert=True)

@callback_check_the_documents_for_the_car_router.callback_query(F.data == "accept_the_documents_car_provider")
async def accept_the_documents_car_provider(callback: CallbackQuery, state: FSMContext, bot: Bot):
    async with deals_session() as session:
        text = callback.message.text
        deal_id = int(text.split('\n')[0].split('Сделка №: ')[1])
        await state.update_data(deal_id=deal_id)
        deals = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deals = deals.scalar_one_or_none()

        deals.confirmation_of_acceptance_of_documents_from_suppliers = "Документы приняты"

        await session.commit()
        builder = InlineKeyboardBuilder()
        builder.button(text="Загрузить CMR", callback_data="load_cmr_file")
        builder.button(text="Написать УИН", callback_data="load_uin_text")
        builder.adjust(1)
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Документы Приняты ✅",
            reply_markup=builder.as_markup()
        )
        message_text = (
            f"Сделка №: {deals.deal_id}\n"
            f"Покупатель: {deals.buy_user}\n"
            f"Автомобиль: {deals.march_model}\n"
            f"VIN: {deals.vin_code}\n"
        )
        await bot.send_message(
            chat_id=deals.provider_id,
            text=f"{message_text}\n\n"
                 f"Документы приняты брокером ✅\n"
                 f"⚠️ Ожидайте получения CMR и УИН."
        )

@callback_check_the_documents_for_the_car_router.callback_query(F.data == "load_cmr_file")
async def load_cmr_file(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Загрузите СMR файл")
    await callback.answer(text="Загрузите СMR файл", show_alert=True)
    await state.set_state(Broker.waiting_for_cmr_file)

@callback_check_the_documents_for_the_car_router.message(Broker.waiting_for_cmr_file)
async def waiting_for_cmr_file(message: Message, state: FSMContext, bot: Bot):
    if not message.document:
        await message.answer(text="Нужно отправить файл")
        return
    data = await state.get_data()
    deal_id = data["deal_id"]
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if deal:
            message_text = (
                f"Сделка №: {deal.deal_id}\n"
                f"Покупатель: {deal.buy_user}\n"
                f"Автомобиль: {deal.march_model}\n"
                f"VIN: {deal.vin_code}\n"
            )
            deal.cmr_file = message.document.file_id
            await session.commit()
            await bot.send_document(
                chat_id=deal.provider_id,
                document=deal.cmr_file,
                caption=f"✅ CMR Файл для автомобиля:\n\n"
                        f"{deal.march_model}\n\n"
                        f"{deal.vin_code}"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="⬅️ Назад в Меню", callback_data=f"list_broker_check_deal_{deal_id}")
            builder.adjust(1)
            if deal.uin_text:
                await message.answer("✅ Документ Загружен и отправлен Поставщику", reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                builder.button(text="Написать УИН", callback_data="load_uin_text")
                await message.answer(text=f"{message_text}\n\n"
                                          f"✅ Документ Загружен и отправлен Поставщику\n\n"
                                          "⚠️ Поставщик ожидает УИН, нажмите кнопку <Написать УИН> и напишите код",
                                     reply_markup=builder.as_markup())






@callback_check_the_documents_for_the_car_router.callback_query(F.data == "load_uin_text")
async def load_uin_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text="Напишите УИН код 1 сообщением:")
    await callback.answer(text="Напишите УИН код 1 сообщением", show_alert=True)
    await state.set_state(Broker.waiting_for_uin_text)

@callback_check_the_documents_for_the_car_router.message(Broker.waiting_for_uin_text)
async def waiting_for_uin_text(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        await message.answer(text="Нужно Написать код 1 сообщением")
        return
    data = await state.get_data()
    deal_id = data["deal_id"]
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if deal:
            message_text = (
                f"Сделка №: {deal.deal_id}\n"
                f"Покупатель: {deal.buy_user}\n"
                f"Автомобиль: {deal.march_model}\n"
                f"VIN: {deal.vin_code}\n"
            )
            deal.uin_text = message.text
            await session.commit()
            await bot.send_message(
                chat_id=deal.provider_id,
                text=f"УИН код:\n\n"
                     f"✅ {message.text}\n\n"
                     f"Для Автомобиля:\n"
                     f"{deal.march_model}\n"
                     f"{deal.vin_code}"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="⬅️ Назад в Меню", callback_data=f"list_broker_check_deal_{deal_id}")
            builder.adjust(1)
            if deal.cmr_file:
                await message.answer(f"✅ УИН: {message.text} отправлен Поставщику", reply_markup=builder.as_markup())
            else:
                builder = InlineKeyboardBuilder()
                builder.button(text="Загрузить CMR", callback_data="load_cmr_file")
                await message.answer(text=f"{message_text}\n\n"
                                          f"✅ УИН код < {message.text} > отправлен Поставщику\n\n"
                                          "⚠️ Поставщик ожидает CMR файл, нажмите кнопку ниже <Загрузить CMR> и отправьте файл",
                                     reply_markup=builder.as_markup())



@callback_check_the_documents_for_the_car_router.callback_query(F.data == "reject_the_documents_car_provider")
async def reject_the_documents_car_provider(callback: CallbackQuery, state: FSMContext):
    async with deals_session() as session:
        text = callback.message.text
        deal_id = int(text.split('\n')[0].split('Сделка №: ')[1])
        deals = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deals = deals.scalar_one_or_none()

        deals.confirmation_of_acceptance_of_documents_from_suppliers = ""

        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Документы не приняты ❌",
            reply_markup=None
        )
        await callback.message.answer(
            text="Напишите ОДНИМ СООБЩЕНИЕМ, что нужно исправить для принятия документов:"
        )
        await state.update_data(deal_id=deals.deal_id)
        await state.set_state(Broker.waiting_for_reason_provider)


@callback_check_the_documents_for_the_car_router.message(Broker.waiting_for_reason_provider)
async def waiting_for_reason_provider(message: Message, state: FSMContext):

    await state.update_data(reason=message.text)

    builder = InlineKeyboardBuilder()
    builder.button(text="Верно ✅", callback_data="accept_the_reason_provider")
    builder.button(text="Написать заново ❌", callback_data="reject_the_reason_provider")

    await message.answer(
        text=f"Вы указали причину отказа принятия документов:\n\n"
             f"{message.text}\n\n"
             f"Верно?",
        reply_markup=builder.as_markup()
    )

@callback_check_the_documents_for_the_car_router.callback_query(F.data == "accept_the_reason_provider")
async def accept_the_reason_provider(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    deal_id = data["deal_id"]
    reason = data["reason"]
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deals = deals.scalar_one_or_none()
        message_text = (
            f"Сделка №: {deals.deal_id}\n"
            f"Покупатель: {deals.buy_user}\n"
            f"Автомобиль: {deals.march_model}\n"
            f"VIN: {deals.vin_code}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="Исправлено ✅", callback_data="fixed_it_document_provider")
        await bot.send_photo(
            chat_id=deals.provider_id,
            photo=deals.car_photo_id,
            caption=f"{message_text}\n\n"
                    f"⚠️ДОКУМЕНТЫ ПО АВТО НЕ ПРИНЯТЫ ❌ БРОКЕРОМ ⚠️\n\n"
                    f"{reason}\n\n"
                    f"Исправьте все прописанные Брокером исправления и нажмите кнопку ниже Исправлено ✅",
            reply_markup=builder.as_markup()
        )
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Поставщик получил уведомление с пояснениями.",
            reply_markup=None
        )
        await state.clear()

@callback_check_the_documents_for_the_car_router.callback_query(F.data == "fixed_it_document_provider")
async def fixed_it_document_provider(callback: CallbackQuery, bot: Bot):
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
        builder.button(text="🔍 Проверить документы", callback_data="check_the_documents_for_the_car")
        await bot.send_photo(
            chat_id=deals.broker_id,
            photo=deals.car_photo_id,
            caption=f"{message_text}\n\n"
                    f"Поставщик исправил недочёты ✅\n"
                    f"Пожалуйста проверьте документы снова",
            reply_markup=builder.as_markup()
        )
        await callback.message.edit_reply_markup()
        await callback.message.answer(text=f"{message_text}\n\n"
                                              f"Брокер получил уведомление об исправлении документов ✅")

@callback_check_the_documents_for_the_car_router.callback_query(F.data == "reject_the_reason_provider")
async def reject_the_reason_provider(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        text="Напишите ОДНИМ СООБЩЕНИЕМ, что нужно исправить для принятия документов:"
    )