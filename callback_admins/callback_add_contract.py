from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Admin
from data_base.db_deals import deals_session, Deals

callback_add_contract_router = Router()

@callback_add_contract_router.callback_query(F.data == "add_contract")
async def add_contract(callback: CallbackQuery, state: FSMContext):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()

    await state.update_data(deal_id=deal_id)
    await state.update_data(photos=[])
    await state.update_data(docs=[])
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="ЗАВЕРШИТЬ ЗАГРУЗКУ"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await callback.message.answer(text="Загрузите фотографии или сканы Договора на автомобиль\n\n"
                                       "По завершению загрузки нажмите ЗАВЕРШИТЬ ЗАГРУЗКУ",
                                  reply_markup=reply_markup)
    await state.set_state(Admin.waiting_for_load_contract)
    await callback.message.delete()


@callback_add_contract_router.message(Admin.waiting_for_load_contract)
async def add_contract_load(message: Message, state: FSMContext):
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
                deal.contract_photo_id = photos
                deal.contract_docs_id = docs
                await session.commit()
                builder = InlineKeyboardBuilder()
                builder.button(text="Назад к списку сделок", callback_data="admin_all_orders")
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
        await message.answer("Отправьте Фото или Видео")