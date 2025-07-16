import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select

from core.state_fsm import Broker
from data_base.db_deals import deals_session, Deals

callback_check_the_buyer_documents_router = Router()

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
            deals = await session.execute(
                select(Deals).where(deal_id == Deals.deal_id)
            )
            deals = deals.scalar_one_or_none()

            # Если нет ни фото, ни документов
            if not deals.passport_photos and not deals.passport_documents and not deals.foreign_currency_account_statement_photo and not deals.foreign_currency_account_statement_docs and not deals.cash_flow_statement_photos and not deals.cash_flow_statement_docs and not deals.snils_buyer_photos and not deals.snils_buyer_docs and not deals.buyer_phone_number and not deals.elpts_registration_photo:
                await callback.answer("Документы ещё не загружены Поставщиком", show_alert=True)
                return

            if deals.buyer_phone_number:
                await callback.message.answer(
                    text="Анкета Покупателя:\n\n"
                         f"Заказчик: {deals.buy_user}\n"
                         f"Номер телефона: {deals.buyer_phone_number}\n"
                         f"Фактический адрес проживания: {deals.buyer_actual_address_of_residence}\n"
                         f"E-mail: {deals.buyer_email_address}\n"
                         f"Серия и номер ВУ: {deals.buyer_driver_license}\n"
                         f"Был ли ввоз автомобиля из-за границы за последние 3 года: {deals.buyer_imported_yes_no}\n"
                         f"Есть ли автомобиль в пользовании в данный момент: {deals.buyer_have_car}\n"

                )

            # Квитанция об оплате автомобиля
            if deals.payment_photo_id:
                photo_group = MediaGroupBuilder(caption="Фото Квитанции об оплате автомобиля:")
                for photo_id in deals.payment_photo_id:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

            if deals.payment_document_id:
                doc_group = MediaGroupBuilder(caption="Скан Квитанции об оплате автомобиля:")
                for doc_id in deals.payment_document_id:
                    doc_group.add_document(media=doc_id)
                await callback.message.answer_media_group(media=doc_group.build())

            # ПАСПОРТ
            if deals.passport_photos:
                photo_group = MediaGroupBuilder(caption="Фото ПАСПОРТА:")
                for photo_id in deals.passport_photos:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

            if deals.passport_documents:
                doc_group = MediaGroupBuilder(caption="Сканы ПАСПОРТА:")
                for doc_id in deals.passport_documents:
                    doc_group.add_document(media=doc_id)
                await callback.message.answer_media_group(media=doc_group.build())

            # Водительское Удостоверение
            if deals.buyer_driver_license_photo:
                photo_group = MediaGroupBuilder(caption="Фото Водительского Удостоверения:")
                for photo_id in deals.buyer_driver_license_photo:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

            if deals.buyer_driver_license_docs:
                photo_group = MediaGroupBuilder(caption="Сканы Водительского Удостоверения:")
                for photo_id in deals.buyer_driver_license_docs:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

            # Выписки по валютному счёту
            if deals.foreign_currency_account_statement_photo:
                photo_group = MediaGroupBuilder(caption="Фото Выписки по валютному счёту:")
                for photo_id in deals.foreign_currency_account_statement_photo:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

            if deals.foreign_currency_account_statement_docs:
                doc_group = MediaGroupBuilder(caption="Сканы Выписки по валютному счёту:")
                for doc_id in deals.foreign_currency_account_statement_docs:
                    doc_group.add_document(media=doc_id)
                await callback.message.answer_media_group(media=doc_group.build())

            # Выписки движения денег по валютному счёту
            if deals.cash_flow_statement_photos:
                photo_group = MediaGroupBuilder(caption="Фото Выписки движения денег по валютному счёту:")
                for photo_id in deals.cash_flow_statement_photos:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

            if deals.cash_flow_statement_docs:
                doc_group = MediaGroupBuilder(caption="Сканы Выписки движения денег по валютному счёту:")
                for doc_id in deals.cash_flow_statement_docs:
                    doc_group.add_document(media=doc_id)
                await callback.message.answer_media_group(media=doc_group.build())

            # СНИЛС
            if deals.snils_buyer_photos:
                photo_group = MediaGroupBuilder(caption="Фото СНИЛС:")
                for photo_id in deals.snils_buyer_photos:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

            if deals.snils_buyer_docs:
                doc_group = MediaGroupBuilder(caption="Сканы СНИЛС:")
                for doc_id in deals.snils_buyer_docs:
                    doc_group.add_document(media=doc_id)
                await callback.message.answer_media_group(media=doc_group.build())

            # Фото регистрации в ЭПТС
            if deals.elpts_registration_photo:
                photo_group = MediaGroupBuilder(caption="Фото регистрации в ЭПТС:")
                for photo_id in deals.elpts_registration_photo:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

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
        logging.error(f"Error in сheck_the_documents_for_the_car: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@callback_check_the_buyer_documents_router.callback_query(F.data == "accept_the_documents_buyer")
async def accept_the_documents_buyer(callback: CallbackQuery):
    async with deals_session() as session:
        text = callback.message.text
        deal_id = int(text.split('\n')[0].split('Сделка №: ')[1])
        deals = await session.execute(
            select(Deals).where(deal_id == Deals.deal_id)
        )
        deals = deals.scalar_one_or_none()

        deals.confirmation_of_acceptance_of_documents_from_buyer = "Документы приняты"

        await session.commit()
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Документы Приняты ✅"
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
        await bot.send_photo(
            chat_id=deals.buyer_id,
            photo=deals.car_photo_id,
            caption=f"{message_text}\n\n"
                    f"⚠️ВАШИ ДОКУМЕНТЫ НЕ ПРИНЯТЫ ❌ БРОКЕРОМ ⚠️\n\n"
                    f"{reason}"
        )
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Покупатель получил уведомление с пояснениями.",
            reply_markup=None
        )
        await state.clear()

@callback_check_the_buyer_documents_router.callback_query(F.data == "reject_the_reason_provider")
async def reject_the_reason_buyer(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        text="Напишите ОДНИМ СООБЩЕНИЕМ, что нужно исправить для принятия документов:"
    )