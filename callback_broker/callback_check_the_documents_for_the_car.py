import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals

callback_check_the_documents_for_the_car_router = Router()


@callback_check_the_documents_for_the_car_router.callback_query(F.data == "сheck_the_documents_for_the_car")
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
            if not deals.photo_docs_car_provider_id and not deals.document_docs_car_provider_id:
                await callback.answer("Документы ещё не загружены Поставщиком", show_alert=True)
                return

            # Создаем отдельные медиагруппы для фото и документов
            if deals.photo_docs_car_provider_id:
                photo_group = MediaGroupBuilder(caption="Фото документов:")
                for photo_id in deals.photo_docs_car_provider_id:
                    photo_group.add_photo(media=photo_id)
                await callback.message.answer_media_group(media=photo_group.build())

            if deals.document_docs_car_provider_id:
                doc_group = MediaGroupBuilder(caption="Сканы документов:")
                for doc_id in deals.document_docs_car_provider_id:
                    doc_group.add_document(media=doc_id)
                await callback.message.answer_media_group(media=doc_group.build())

            await callback.answer()

    except Exception as e:
        logging.error(f"Error in сheck_the_documents_for_the_car: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)
