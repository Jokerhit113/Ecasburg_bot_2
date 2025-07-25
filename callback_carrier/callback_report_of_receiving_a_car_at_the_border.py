from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Carrier
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_report_of_receiving_a_car_at_the_border_router = Router()


@callback_report_of_receiving_a_car_at_the_border_router.callback_query(F.data == "report_of_receiving_a_car_at_the_border")
async def report_of_receiving_a_car_at_the_border(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Перевозчик выбрал Загрузить Фото получения авто с Таможни")
    caption = callback.message.caption
    deal_id = caption.split('\n')[0].split('Сделка №: ')[1]
    await state.update_data(deal_id=deal_id)
    await state.update_data(photos = [])
    await state.update_data(videos = [])
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await callback.message.answer(text="Загрузите фотографии или видео автомобиля перед погрузкой:\n\n"
                                       "По завершению загрузки нажмите ЗАВЕРШИТЬ ЗАГРУЗКУ",
                                  reply_markup=reply_markup)
    await state.set_state(Carrier.waiting_for_get_report_get_car)
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=f"deal_list_carrier_{deal_id}")
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())

@callback_report_of_receiving_a_car_at_the_border_router.message(Carrier.waiting_for_get_report_get_car)
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
                deal.photo_car_get_border = photos
                deal.video_car_get_border = videos
                await session.commit()
                await message.answer(
                    text=f"✅ Успешно сохранено:\n"
                         f" {len(photos)} Фото\n"
                         f"{len(videos)} Видео"                )
            else:
                await message.answer(text="Сделка не найдена")

            await message.answer(text=f"Загрузка завершена",
                                 reply_markup=ReplyKeyboardRemove())
            await state.set_state(Carrier.waiting_for_get_car_comments)
            await message.answer("Напиши одним сообщением комментарии к получению автомобиля на границе:\n\n"
                                 "Например: Царапина / 1 ключ / Не хватает документов и т.д.\n"
                                 "Если нареканий нет, то напиши что Всё хорошо!.")
    else:
        await message.answer("Отправьте Фото или Видео")


@callback_report_of_receiving_a_car_at_the_border_router.message(Carrier.waiting_for_get_car_comments)
async def waiting_for_get_car_comments(message: Message, state: FSMContext, bot: Bot):
    if not message.text:
        await message.answer("Напишите Ваши впечатления одним текстом:")
        return
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{message.from_user.first_name} {message.from_user.last_name} Перевозчик Написал комментарий к получению автомобиля: {message.text}")
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Верно", callback_data="feedback_carrier_ok")
    builder.button(text="🚫 Написать Заново", callback_data="delete_message")
    await state.update_data(feedback_carrier_text=message.text)
    await message.answer(text=f"Вы написали:"
                              f"\n\n{message.text}\n\n"
                              f"Верно?",
                         reply_markup=builder.as_markup())

@callback_report_of_receiving_a_car_at_the_border_router.callback_query(F.data == "feedback_carrier_ok")
async def feedback_carrier_ok(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    deal_id = data['deal_id']
    feedback_carrier_text = data['feedback_carrier_text']
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Перевозчик подтвердил комментарий к получению автомобиля:\n\n "
                                f"{feedback_carrier_text}")
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer("Сделка не найдена")
            return
        deal.comments_carrier = feedback_carrier_text
        await session.commit()
        await callback.message.delete_reply_markup()
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ В меню", callback_data=f"deal_list_carrier_{deal_id}")
        await callback.message.answer(text="Данные сохранены ✅", reply_markup=builder.as_markup())

        await state.clear()
