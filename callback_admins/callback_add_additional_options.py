from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Admin
from data_base.db_deals import deals_session, Deals

callback_add_additional_options_router = Router()

@callback_add_additional_options_router.callback_query(F.data == "add_additional_options")
async def add_additional_options(callback: CallbackQuery, state: FSMContext):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
            await state.update_data(deal_id=deal_id)
    await callback.answer("Напишите одним текстом какие Опции нужно добавить к автомобилю:", show_alert=True)
    await callback.message.answer(text="Напишите одним текстом какие Опции нужно добавить к автомобилю:")
    await state.set_state(Admin.waiting_for_text_additional_options)

@callback_add_additional_options_router.message(Admin.waiting_for_text_additional_options)
async def waiting_for_text_additional_options(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Напишите одним текстом какие доп опции нужно добавить:")
        return
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="Добавить ✅"))
    reply_builder.add(KeyboardButton(text="Заполнить заново ❌"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await message.answer(f"Вы хотите добавить к автомобилю следующие Дополнительные опции:\n\n"
                         f"{message.text}\n\n"
                         f"Верно?",
                         reply_markup=reply_markup)
    await state.update_data(additional_options=message.text)
    await state.set_state(Admin.waiting_for_text_additional_options_yes_no)

@callback_add_additional_options_router.message(Admin.waiting_for_text_additional_options_yes_no)
async def waiting_for_text_additional_options_yes_no(message: Message, state: FSMContext):
    if not message.text:
        await message.answer(text="Выберите Добавить / Заполнить заново")
        return
    data = await state.get_data()
    deal_id = data.get("deal_id")
    additional_options = data.get("additional_options")
    if message.text == "Добавить ✅":
        async with deals_session() as session:
            deal = await session.execute(select(Deals).where(Deals.deal_id == deal_id))
            deal = deal.scalar_one_or_none()
            if deal:
                deal.additional_options = additional_options
                await session.commit()
                await message.answer(text=f"Доп. опции:\n\n"
                                          f"{additional_options}\n\n"
                                          f"✅ Добавлены к заказу",
                                     reply_markup=ReplyKeyboardRemove())
                builder = InlineKeyboardBuilder()
                builder.button(text="Назад в Меню", callback_data=f"deal_detail_{deal.id}")
                builder.adjust(1)
                await message.answer(text="Нажмите кнопку ниже что бы вернуться в меню",
                                     reply_markup=builder.as_markup())
                await state.clear()
    if message.text == "Заполнить заново ❌":
        await state.set_state(Admin.waiting_for_text_additional_options)
        await message.answer(text="Напишите одним текстом какие доп опции нужно добавить:",
                             reply_markup=ReplyKeyboardRemove())

