from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Provider
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_car_go_to_rf_router = Router()

@callback_car_go_to_rf_router.callback_query(F.data == "car_go_to_rf")
async def car_go_to_rf(callback: CallbackQuery, state: FSMContext):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
    await state.update_data(deal_id=deal_id)
    await state.update_data(photos=[])
    await state.update_data(videos=[])
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await callback.message.answer(text="Загрузите фотографии или видео до отправки автомобиля до границы:\n\n"
                                       "По завершению загрузки нажмите ЗАВЕРШИТЬ ЗАГРУЗКУ",
                                  reply_markup=reply_markup)
    await state.set_state(Provider.waiting_for_car_go_to_rf)
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=f"check_deal_{deal_id}")
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())


@callback_car_go_to_rf_router.message(Provider.waiting_for_car_go_to_rf)
async def car_go_to_rf_get_photo_video(message: Message, state: FSMContext):
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
                deal.car_go_to_rf_photo = photos
                deal.car_go_to_rf_video = videos
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
                await message.answer("⬅️ Назад", reply_markup=builder.as_markup())

            else:
                await message.answer(text="Сделка не найдена")

    else:
        await message.answer("Отправьте Фото или Видео")
