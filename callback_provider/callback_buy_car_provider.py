

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Provider
from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_provider_main
from settings import CHAT_LOG

callback_buy_car_provider_router = Router()

@callback_buy_car_provider_router.callback_query(F.data == "buy_car_provider")
async def buy_car_provider(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Поставщик выбрал Загрузить фото выкупа автомобиля")
    caption = callback.message.caption
    deal_id = caption.split('\n')[0].split('Сделка №: ')[1]
    await state.update_data(deal_id=deal_id)
    await state.update_data(photos = [])
    await state.update_data(videos = [])
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="COMPLETE THE UPLOAD"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await callback.message.answer(text="Upload photos or videos of the car buyback:\n\n"
                                       "When the upload is complete, click COMPLETE THE UPLOAD",
                                  reply_markup=reply_markup)
    await state.set_state(Provider.waiting_for_photo_buy_car)
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back", callback_data=f"check_deal_{deal_id}")
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

@callback_buy_car_provider_router.message(Provider.waiting_for_photo_buy_car)
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

    elif message.video:
        data = await state.get_data()
        videos = data.get('videos', [])
        videos.append(message.video.file_id)
        await state.update_data(videos=videos)
        await message.answer(text=f"Video added. Total: {len(videos)}",
                             reply_markup=reply_markup)

    elif message.text == "COMPLETE THE UPLOAD":
        data = await state.get_data()
        deal = data.get('deal_id')
        photos = data.get('photos', [])
        videos = data.get('videos', [])

        if not photos and not videos:
            await message.answer("You haven't sent any photos or files!", reply_markup=ReplyKeyboardRemove())
            return
        async with deals_session() as session:
            deal = await session.execute(select(Deals).where(Deals.deal_id == deal))
            deal = deal.scalar_one_or_none()

            if deal:
                deal.buy_car_provider_photo_id = photos
                deal.buy_car_provider_video_id = videos
                await session.commit()
                await message.answer(
                    text=f"✅ Saved successfully:\n"
                         f" {len(photos)} Photo\n"
                         f"{len(videos)} Video"
                )
                await message.answer(text=f"The upload is completed",
                                     reply_markup=ReplyKeyboardRemove())
                await message.answer(text="Please specify the delivery time for the purchased car:\n\n"
                                          "For example: 5 - 7 days")
                await state.set_state(Provider.waiting_for_delivery_time_car_to_provider)

            else:
                await message.answer(text="The transaction was not found")




    else:
        await message.answer("Send a Photo or Video")

@callback_buy_car_provider_router.message(Provider.waiting_for_delivery_time_car_to_provider)
async def delivery_time_car_to_provider(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

    await state.update_data(delivery_time_car_to_provider=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ That's right", callback_data="add_delivery_time_car_to_provider")
    builder.button(text="❌ Fill It Out Again", callback_data="again_text_to_provider")
    builder.adjust(1)
    await message.answer(text="You have indicated that the car you have purchased will be delivered to you via:\n\n"
                              f"{message.text}\n\n"
                              f"Right?",
                         reply_markup=builder.as_markup())

@callback_buy_car_provider_router.callback_query(F.data == "add_delivery_time_car_to_provider")
async def add_delivery_time_car_to_provider(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Поставщик Подтвердил срок доставки автомобиля до Поставщика ")
    async with deals_session() as session:
        data = await state.get_data()
        deal = data.get('deal_id')
        delivery_time_car_to_provider_user = data.get('delivery_time_car_to_provider')
        deal = await session.execute(select(Deals).where(Deals.deal_id == deal))
        deal = deal.scalar_one_or_none()
        if deal:
            deal.delivery_time_car_to_provider = delivery_time_car_to_provider_user
            await session.commit()
            await callback.answer(f"Car delivery time {delivery_time_car_to_provider_user}")
            await callback.message.edit_text(text=f"{callback.message.text}\n\n"
                                                  f"The delivery time to the Supplier has been confirmed!",
                                             reply_markup=kb_provider_main)
            await state.clear()
        else:
            await callback.answer(text="The transaction was not found")

@callback_buy_car_provider_router.callback_query(F.data == "again_text_to_provider")
async def again_text(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(text="Write the delivery time again")