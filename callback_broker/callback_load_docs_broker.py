from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Broker
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_load_docs_broker_router = Router()

@callback_load_docs_broker_router.callback_query(F.data == "load_docs_broker")
async def load_docs_broker(callback: CallbackQuery, state: FSMContext, bot: Bot):
    caption = callback.message.caption
    deal_id = caption.split('\n')[0].split('Сделка №: ')[1]
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Брокер Выбрал загрузить Документы по сделке {deal_id}")
    await state.update_data(deal_id=deal_id)
    await state.update_data(photos = [])
    await state.update_data(docs = [])
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await callback.message.answer(text="Загрузите фотографии или сканы документов на автомобиль\n\n"
                                       "По завершению загрузки нажмите ЗАВЕРШИТЬ ЗАГРУЗКУ",
                                  reply_markup=reply_markup)
    await state.set_state(Broker.waiting_for_documents_broker)
    await callback.message.delete()


@callback_load_docs_broker_router.message(Broker.waiting_for_documents_broker)
async def photo_video_buy_car(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)

    if message.photo:
        data = await state.get_data()
        photos = data.get('photos', [])
        photos.append(message.photo[-1].file_id)
        await state.update_data(photos=photos)
        await message.answer(text=f"Фото добавлено. Всего: {len(photos)}",
                             reply_markup=reply_markup)

    elif message.document:
        data = await state.get_data()
        docs = data.get('docs', [])
        docs.append(message.document.file_id)
        await state.update_data(docs=docs)
        await message.answer(text=f"Документ загружен. Всего: {len(docs)}",
                             reply_markup=reply_markup)

    elif message.text == "ЗАВЕРШИТЬ ЗАГРУЗКУ":
        data = await state.get_data()
        deal = data.get('deal_id')
        photos = data.get('photos', [])
        docs = data.get('docs', [])

        if not photos and not docs:
            await message.answer("Вы не отправили ни одного фото и файла!", reply_markup=ReplyKeyboardRemove())
            return
        async with deals_session() as session:
            deal = await session.execute(select(Deals).where(Deals.deal_id == deal))
            deal = deal.scalar_one_or_none()

            if deal:
                deal.photo_docs_broker_id = photos
                deal.document_doc_broker_id = docs
                await session.commit()
                builder = InlineKeyboardBuilder()
                builder.button(text="⬅️ Назад к списку сделок", callback_data="check_deals_broker")
                builder.adjust(1)
                await message.answer(
                    text=f"✅ Успешно сохранено:\n"
                         f" {len(photos)} Фото\n"
                         f"{len(docs)} Документов",
                    reply_markup=builder.as_markup()
                )
            else:
                await message.answer(text="Сделка не найдена")

            await state.clear()
            await message.answer(text=f"Загрузка завершена",
                                 reply_markup=ReplyKeyboardRemove())


    else:
        await message.answer("Отправьте Фото или Сканы")