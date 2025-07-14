import logging
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select

from core.state_fsm import Broker
from data_base.db_deals import deals_session, Deals

callback_check_the_documents_for_the_car_router = Router()


@callback_check_the_documents_for_the_car_router.callback_query(F.data == "сheck_the_documents_for_the_car")
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
        logging.error(f"Error in сheck_the_documents_for_the_car: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@callback_check_the_documents_for_the_car_router.callback_query(F.data == "accept_the_documents_car_provider")
async def accept_the_documents_car_provider(callback: CallbackQuery):
    async with deals_session() as session:
        text = callback.message.text
        deal_id = int(text.split('\n')[0].split('Сделка №: ')[1])
        deals = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deals = deals.scalar_one_or_none()

        deals.confirmation_of_acceptance_of_documents_from_suppliers = "Документы приняты"

        await session.commit()
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Документы Приняты ✅"
        )

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
        await bot.send_photo(
            chat_id=deals.provider_id,
            photo=deals.car_photo_id,
            caption=f"{message_text}\n\n"
                    f"⚠️ДОКУМЕНТЫ ПО АВТО НЕ ПРИНЯТЫ ❌ БРОКЕРОМ ⚠️\n\n"
                    f"{reason}"
        )
        await callback.message.edit_text(
            text=f"{callback.message.text}\n\n"
                 f"Поставщик получил уведомление с пояснениями.",
            reply_markup=None
        )
        await state.clear()

@callback_check_the_documents_for_the_car_router.callback_query(F.data == "reject_the_reason_provider")
async def reject_the_reason_provider(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        text="Напишите ОДНИМ СООБЩЕНИЕМ, что нужно исправить для принятия документов:"
    )