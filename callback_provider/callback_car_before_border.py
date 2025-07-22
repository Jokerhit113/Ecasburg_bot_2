from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Provider
from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_provider_main

callback_car_before_border_router = Router()

@callback_car_before_border_router.callback_query(F.data == "media_car_before_border")
async def buy_car_provider(callback: CallbackQuery, state: FSMContext):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
    await state.update_data(deal_id=deal_id)
    await state.update_data(photos = [])
    await state.update_data(videos = [])
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await callback.message.answer(text="Загрузите фотографии или видео до отправки автомобиля до границы:\n\n"
                                       "По завершению загрузки нажмите ЗАВЕРШИТЬ ЗАГРУЗКУ",
                                  reply_markup=reply_markup)
    await state.set_state(Provider.waiting_for_car_before_border)
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=f"check_deal_{deal_id}")
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

@callback_car_before_border_router.message(Provider.waiting_for_car_before_border)
async def photo_video_buy_car(message: Message, state: FSMContext):
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

    elif message.video:
        data = await state.get_data()
        videos = data.get('videos', [])
        videos.append(message.video.file_id)
        await state.update_data(videos=videos)
        await message.answer(text=f"Видео добавлено. Всего: {len(videos)}",
                             reply_markup=reply_markup)

    elif message.text == "ЗАВЕРШИТЬ ЗАГРУЗКУ":
        data = await state.get_data()
        deal = data.get('deal_id')
        photos = data.get('photos', [])
        videos = data.get('videos', [])

        if not photos and not videos:
            await message.answer("Вы не отправили ни одного фото и файла!", reply_markup=ReplyKeyboardRemove())
            return
        async with deals_session() as session:
            deal = await session.execute(select(Deals).where(Deals.deal_id == deal))
            deal = deal.scalar_one_or_none()

            if deal:
                deal.provider_photo_car_before_border_id = photos
                deal.provider_video_car_before_border_id = videos
                await session.commit()
                builder = InlineKeyboardBuilder()
                builder.button(text="Back to deal", callback_data=f"check_deal_{deal.deal_id}")
                builder.adjust(1)
                await message.answer(
                    text=f"✅ Успешно сохранено:\n"
                         f" {len(photos)} Фото\n"
                         f"{len(videos)} Видео",
                    reply_markup=builder.as_markup()
                )
                await message.answer(text=f"Загрузка завершена",
                                     reply_markup=ReplyKeyboardRemove())
                await message.answer(text="Напишите срок доставки автомобиля до Границы:\n\n"
                                          "Например: 5 - 7 дней")
                await state.set_state(Provider.waiting_for_delivery_time_car_to_border)

            else:
                await message.answer(text="Сделка не найдена")

    else:
        await message.answer("Отправьте Фото или Видео")

@callback_car_before_border_router.message(Provider.waiting_for_delivery_time_car_to_border)
async def delivery_time_car_to_border(message: Message, state: FSMContext):
    await state.update_data(delivery_time_car_to_border=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Всё верно", callback_data="add_delivery_time_car_to_border")
    builder.button(text="❌ Заполнить Заново", callback_data="again_text_to_border")
    builder.adjust(1)
    await message.answer(text="Вы указали автомобиль будет доставлен на Границу через:\n\n"
                              f"{message.text}\n\n"
                              f"Верно?",
                         reply_markup=builder.as_markup())

@callback_car_before_border_router.callback_query(F.data == "add_delivery_time_car_to_border")
async def add_delivery_time_car_to_border(callback: CallbackQuery, state: FSMContext):
    async with deals_session() as session:
        data = await state.get_data()
        deal = data.get('deal_id')
        delivery_time_car_to_border_user = data.get('delivery_time_car_to_border')
        deal = await session.execute(select(Deals).where(Deals.deal_id == deal))
        deal = deal.scalar_one_or_none()
        if deal:
            deal.delivery_time_car_to_border = delivery_time_car_to_border_user
            await session.commit()
            await callback.answer(f"Срок доставки авто {delivery_time_car_to_border_user}")
            await callback.message.edit_text(text=f"{callback.message.text}\n\n"
                                                  f"Срок доставки до Границы подтверждён!",
                                             reply_markup=kb_provider_main)
            await state.clear()
        else:
            await callback.answer(text="Сделка не найдена")