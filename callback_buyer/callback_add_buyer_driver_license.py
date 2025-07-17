import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals

callback_add_buyer_driver_license_router = Router()

text_vod_ud_get = "Загрузите Фотографии Вашего Водительского удостоверения с 2 двух сторон, либо отправьте сканы:"

@callback_add_buyer_driver_license_router.callback_query(F.data == "driver_license_load_buyer")
async def callback_driver_license(callback: CallbackQuery, state: FSMContext):
    try:
        caption = callback.message.caption
        deal_id = int(caption.split('\n')[0].split('Ваша Сделка №: ')[1])
        await state.update_data(deal_id=deal_id)
        builder = InlineKeyboardBuilder()
        builder.button(text="Назад в Меню", callback_data=f"deal_list_buyer_{deal_id}")
        builder.adjust(1)

        # Создаем Reply-клавиатуру для "Завершить загрузку"
        reply_builder = ReplyKeyboardBuilder()
        reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
        reply_markup = reply_builder.as_markup(resize_keyboard=True)

        await callback.answer(text="ВНИМАТЕЛЬНО ПРОЧИТАЙТЕ ПРАВИЛА ЗАГРУЗКИ Водительского Удостоверения!", show_alert=True)
        await callback.message.edit_caption(caption=text_vod_ud_get,
                                         reply_markup=builder.as_markup())
        await callback.message.answer(text="Загрузите Фото или Скан документов, по завершению нажмите кнопу ЗАВЕРШИТЬ ЗАГРУЗКУ!",
                                      reply_markup=reply_markup)
        await state.update_data(photos=[])
        await state.update_data(documents=[])
        await state.set_state(Buyer.waiting_for_driver_license)

    except Exception as e:
        logging.error(f"Error in callback_driver_license: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)

@callback_add_buyer_driver_license_router.message(Buyer.waiting_for_driver_license)
async def get_photo_or_doc_driver_license(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        deal_id = data.get('deal_id')
        reply_builder = ReplyKeyboardBuilder()
        reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
        reply_markup = reply_builder.as_markup(resize_keyboard=True)
        if message.photo:
            data = await state.get_data()
            photos = data.get('photos', [])
            photos.append(message.photo[-1].file_id)  # Добавляем file_id последнего (самого качественного) фото
            await state.update_data(photos=photos)
            await message.answer(text=f"Фото добавлено. Всего: {len(photos)}",
                                 reply_markup=reply_markup)
        elif message.document:
            data = await state.get_data()
            documents = data.get('documents', [])
            documents.append(message.document.file_id)  # Добавляем file_id последнего (самого качественного) фото
            await state.update_data(documents=documents)
            await message.answer(text=f"Документ добавлен. Всего: {len(documents)}",
                                 reply_markup=reply_markup)
        elif message.text == "ЗАВЕРШИТЬ ЗАГРУЗКУ":
            data = await state.get_data()
            photos = data.get('photos', [])
            documents = data.get('documents', [])

            if not photos and not documents:
                await message.answer("Вы не отправили ни одного фото и файла!", reply_markup=ReplyKeyboardRemove())
                return
            async with deals_session() as session:
                deal = await session.execute(
                    select(Deals).where(Deals.deal_id == deal_id)
                )
                deal = deal.scalar_one_or_none()

                if deal:
                    deal.buyer_driver_license_photo = photos  # Сохраняем весь список
                    deal.buyer_driver_license_docs = documents
                    await session.commit()
                    builder = InlineKeyboardBuilder()
                    builder.button(text="Назад к списку Сделок", callback_data="check_deals_buyer")
                    builder.adjust(1)
                    await message.answer(
                        text=f"✅ Успешно сохранено:\n"
                             f" {len(photos)} фото\n"
                             f"{len(documents)} документ(-а / -ов)",
                        reply_markup=builder.as_markup()
                    )
                else:
                    await message.answer(text="Сделка не найдена")

            await state.clear()
            await message.answer(text=f"Загрузка завершена",
                                 reply_markup=ReplyKeyboardRemove())
        else:
            await message.answer("Загрузите Фото или Скан документов, по завершению нажмите кнопку ЗАВЕРШИТЬ ЗАГРУЗКУ!")
    except Exception as e:
        logging.error(f"Error in get_photo_or_doc_driver_license: {e}", exc_info=True)
        await message.answer("Произошла ошибка")