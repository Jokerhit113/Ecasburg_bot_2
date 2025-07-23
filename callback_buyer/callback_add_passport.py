import logging
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.state_fsm import NewDeals, Buyer
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_add_passport_router = Router()


text_passport_get = ("Загрузите Фотографии паспорта, либо файл Скан в формате *pdf\n\n"
                    "Заверенная нотариусом копия паспорта (разворот с фото и регистрация по месту жительства)\n"
                    "Соблюдаем правила скана и фото\n"
                    " ⁃ разворот хорошо расправлен\n"
                    " ⁃ нет пальцев и посторонних предметов\n"
                    " ⁃ на белом фоне (белый лист А4)\n"
                    ' ⁃ нет бликов и засветов\n'
                    " ⁃ все 4 края документа в кадре , НЕ ОБРЕЗАНЫ!\n"
                    "В идеале отправлять скан из сканера\n\n")

@callback_add_passport_router.callback_query(F.data == "add_passport")
async def callback_add_passport(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал: Загрузить Паспорт")
    try:
        caption = callback.message.caption
        deal_id = int(caption.split('\n')[0].split('Ваша Сделка №: ')[1])
        await state.update_data(deal_id=deal_id)
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад в Меню", callback_data=f"deal_list_buyer_{deal_id}")
        builder.adjust(1)

        # Создаем Reply-клавиатуру для "Завершить загрузку"
        reply_builder = ReplyKeyboardBuilder()
        reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
        reply_markup = reply_builder.as_markup(resize_keyboard=True)

        await callback.answer(text="ВНИМАТЕЛЬНО ПРОЧИТАЙТЕ ПРАВИЛА ЗАГРУЗКИ ПАСПОРТА!", show_alert=True)
        await callback.message.edit_caption(caption=text_passport_get,
                                         reply_markup=builder.as_markup())
        await callback.message.answer(text="Загрузите Фото или Скан документов, по завершению нажмите кнопу ЗАВЕРШИТЬ ЗАГРУЗКУ!",
                                      reply_markup=reply_markup)
        await state.update_data(photos=[])
        await state.update_data(documents=[])
        await state.set_state(Buyer.waiting_for_get_passport)

    except Exception as e:
        logging.error(f"Error in get_elpts_registration: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)

@callback_add_passport_router.message(Buyer.waiting_for_get_passport)
async def get_photo_or_doc_passport(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

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
                    deal.passport_photos = photos  # Сохраняем весь список
                    deal.passport_documents = documents
                    await session.commit()
                    builder = InlineKeyboardBuilder()
                    builder.button(text="⬅️ Назад к списку Сделок", callback_data="check_deals_buyer")
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
        logging.error(f"Error in get_elpts_registration: {e}", exc_info=True)
        await message.answer("Произошла ошибка")