from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Provider
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_load_docs_car_provider_router = Router()

@callback_load_docs_car_provider_router.callback_query(F.data == "load_docs_car_provider")
async def buy_car_provider(callback: CallbackQuery, state: FSMContext, bot: Bot):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Поставщик Выбрал загрузить документы на автомобиль по сделке {deal_id}")
    await state.update_data(deal_id=deal_id)
    await state.update_data(photos = [])
    await state.update_data(docs = [])
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="COMPLETE THE UPLOAD"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await callback.message.answer(text="Upload photos or scans of your car's documents\n\n"
                                       "When the upload is complete, click COMPLETE THE UPLOAD",
                                  reply_markup=reply_markup)
    await state.set_state(Provider.waiting_for_load_docs_car_provider)
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back", callback_data=f"check_deal_{deal_id}")
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

@callback_load_docs_car_provider_router.message(Provider.waiting_for_load_docs_car_provider)
async def photo_video_buy_car(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="COMPLETE THE UPLOAD"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)

    if message.photo:
        data = await state.get_data()
        photos = data.get('photos', [])
        photos.append(message.photo[-1].file_id)
        await state.update_data(photos=photos)
        await message.answer(text=f"Photo added. Total: {len(photos)}",
                             reply_markup=reply_markup)

    elif message.document:
        data = await state.get_data()
        docs = data.get('docs', [])
        docs.append(message.document.file_id)
        await state.update_data(docs=docs)
        await message.answer(text=f"The document is uploaded. Total: {len(docs)}",
                             reply_markup=reply_markup)

    elif message.text == "COMPLETE THE UPLOAD":
        data = await state.get_data()
        deal = data.get('deal_id')
        photos = data.get('photos', [])
        docs = data.get('docs', [])

        if not photos and not docs:
            await message.answer("You haven't sent any photos or files!", reply_markup=ReplyKeyboardRemove())
            return
        async with deals_session() as session:
            deal = await session.execute(select(Deals).where(Deals.deal_id == deal))
            deal = deal.scalar_one_or_none()

            if deal:
                deal.photo_docs_car_provider_id = photos
                deal.document_docs_car_provider_id = docs
                await session.commit()
                builder = InlineKeyboardBuilder()
                builder.button(text="Back to deal", callback_data=f"check_deal_{deal.deal_id}")
                builder.adjust(1)
                await message.answer(
                    text=f"✅ Saved successfully:\n"
                         f" {len(photos)} Photo\n"
                         f"{len(docs)} Documents",
                    reply_markup=builder.as_markup()
                )
            else:
                await message.answer(text="The transaction was not found")

            await state.clear()
            await message.answer(text=f"The upload is completed",
                                 reply_markup=ReplyKeyboardRemove())


    else:
        await message.answer("Send a Photo or Video")