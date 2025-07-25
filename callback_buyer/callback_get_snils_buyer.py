import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_get_snils_buyer_router = Router()

text_snils_get = ("Загрузите Фотографии Вашего СНИЛС с 2 двух сторон, либо отправьте сканы:")

@callback_get_snils_buyer_router.callback_query(F.data == "add_snils_buyer")
async def callback_add_passport(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал: Загрузить СНИЛС")
    try:
        caption = callback.message.caption
        deal_id = caption.split('\n')[0].split('Ваша Сделка №: ')[1]
        await state.update_data(deal_id=deal_id)
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад в Меню", callback_data=f"deal_list_buyer_{deal_id}")
        builder.adjust(1)

        # Создаем Reply-клавиатуру для "Завершить загрузку"
        reply_builder = ReplyKeyboardBuilder()
        reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
        reply_markup = reply_builder.as_markup(resize_keyboard=True)

        await callback.answer()
        await callback.message.edit_caption(caption=text_snils_get,
                                         reply_markup=builder.as_markup())
        await callback.message.answer(text="Загрузите Фото или Скан документов, по завершению нажмите кнопу ЗАВЕРШИТЬ ЗАГРУЗКУ!",
                                      reply_markup=reply_markup)
        await state.update_data(photos=[])
        await state.update_data(documents=[])
        await state.set_state(Buyer.waiting_for_get_snils)

    except Exception as e:
        logging.error(f"Error in get_elpts_registration: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)

@callback_get_snils_buyer_router.message(Buyer.waiting_for_get_snils)
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
                    deal.snils_buyer_photos = photos  # Сохраняем весь список
                    deal.snils_buyer_docs = documents
                    await session.commit()
                    builder = InlineKeyboardBuilder()
                    builder.button(text="⬅️ Назад к Сделке", callback_data=f"deal_list_buyer_{deal_id}")
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