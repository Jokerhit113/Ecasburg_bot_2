import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals

callback_check_the_buyer_documents_router = Router()

@callback_check_the_buyer_documents_router.callback_query(F.data == "check_the_buyer_documents")
async def check_the_documents_for_the_car_router(callback: CallbackQuery):
    try:
        caption = callback.message.caption
        deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
        async with deals_session() as session:
            deals = await session.execute(
                select(Deals).where(Deals.deal_id == deal_id)
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

            await callback.answer()



    except Exception as e:
        logging.error(f"Error in сheck_the_documents_for_the_car: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)