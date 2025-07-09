from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals

callback_foreign_currency_account_statement_router = Router()

text_foreign_currency_account_statement_get = (f"Загрузите Фотографии "
                                               f"ВЫПИСКИ ПО ВАЛЮТНОМУ СЧЁТУ")

@callback_foreign_currency_account_statement_router.callback_query(F.data == "foreign_currency_account_statement")
async def foreign_currency_account_statement(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад к списку документов", callback_data="kb_menu_load_docs")
    builder.adjust(1)

    # Создаем Reply-клавиатуру для "Завершить загрузку"
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)

    await callback.answer(text="ВНИМАТЕЛЬНО ПРОЧИТАЙТЕ ПРАВИЛА ЗАГРУЗКИ ВЫПИСКИ ПО ВАЛЮТНОМУ СЧЁТУ!", show_alert=True)
    await callback.message.edit_text(text=text_foreign_currency_account_statement_get,
                                     reply_markup=builder.as_markup())
    await callback.message.answer(text="Загрузите Фото или Скан документов, по завершению нажмите кнопу ЗАВЕРШИТЬ ЗАГРУЗКУ!",
                                  reply_markup=reply_markup)
    await state.update_data(photos=[])
    await state.update_data(documents=[])
    await state.set_state(Buyer.waiting_for_get_foreign_currency_account_statement)


@callback_foreign_currency_account_statement_router.message(Buyer.waiting_for_get_foreign_currency_account_statement)
async def get_photo_or_doc_passport(message: Message, state: FSMContext):
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
                select(Deals).where(Deals.buyer_id == message.from_user.id)
            )
            deal = deal.scalar_one_or_none()

            if deal:
                deal.foreign_currency_account_statement_photo = photos  # Сохраняем весь список
                deal.foreign_currency_account_statement_docs = documents
                await session.commit()
                builder = InlineKeyboardBuilder()
                builder.button(text="Назад к списку документов", callback_data="add_documents_buyer")
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