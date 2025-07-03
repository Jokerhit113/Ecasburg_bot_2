import logging
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import NewDeals
from data_base.db_deals import deals_session, Deals
from keyboard.admins_inline_keyboard import kb_back_to_menu, kb_admin_main

add_new_deal_router = Router()

@add_new_deal_router.callback_query(F.data == "admin_new_order")
async def admin_new_order(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text(
        text="Напишите номер Новой сделки:",
    reply_markup=kb_back_to_menu)
    await state.set_state(NewDeals.waiting_for_id_deal)

@add_new_deal_router.message(NewDeals.waiting_for_id_deal)
async def get_id_new_deal_id(message: Message, state: FSMContext):
    await state.update_data(new_deal_id=message.text)
    await message.answer(
        text="Напишите Фио покупателя:",
    reply_markup=kb_back_to_menu)
    await state.set_state(NewDeals.waiting_for_buyer_name)

@add_new_deal_router.message(NewDeals.waiting_for_buyer_name)
async def get_new_deal_name(message: Message, state: FSMContext):
    await state.update_data(new_deal_name=message.text)
    await message.answer(
        text="Напишите Марку / Модель / Комплектацию автомобиля:",
    reply_markup=kb_back_to_menu)
    await state.set_state(NewDeals.waiting_for_march_car)

@add_new_deal_router.message(NewDeals.waiting_for_march_car)
async def get_new_deal_march_car(message: Message, state: FSMContext):
    await state.update_data(new_deal_march_car=message.text)
    await message.answer(text="Напишите Vin code Автомобиля:",
                         reply_markup=kb_back_to_menu)
    await state.set_state(NewDeals.waiting_for_vin_code)

@add_new_deal_router.message(NewDeals.waiting_for_vin_code)
async def get_new_deal_vin_car(message: Message, state: FSMContext):
    await state.update_data(new_deal_vin_car=message.text)
    await message.answer(text="Отправьте 1 фото автомобиля",
                         reply_markup=kb_back_to_menu)
    await state.set_state(NewDeals.waiting_for_photo_car)

@add_new_deal_router.message(NewDeals.waiting_for_photo_car)
async def get_new_deal_photo_car(message: Message, state: FSMContext):
    await state.update_data(new_deal_photo_car=message.photo[-1].file_id)
    data = await state.get_data()
    deal_id = data.get("new_deal_id")
    buyer_name = data.get("new_deal_name")
    march_car = data.get("new_deal_march_car")
    vin_code = data.get("new_deal_vin_car")
    photo_car = data.get("new_deal_photo_car")

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Добавить сделку ", callback_data="add_new_deal_ok")
    builder.button(text="❌ Назад в меню", callback_data="back_to_menu")
    await message.answer_photo(
        photo=photo_car,
        caption=f"Новая сделка:\n\n"
                f"Сделка №: {deal_id}\n"
                f"Покупатель: {buyer_name}\n"
                f"Автомобиль: {march_car}\n"
                f"Vin Code: {vin_code}\n",
        reply_markup=builder.as_markup())

@add_new_deal_router.callback_query(F.data == "add_new_deal_ok")
async def add_new_deal_ok(callback: CallbackQuery, state: FSMContext, bot: Bot):
    async with deals_session() as session:
        try:
            data = await state.get_data()
            deal_id = data.get("new_deal_id")
            buyer_name = data.get("new_deal_name")
            march_car = data.get("new_deal_march_car")
            vin_code = data.get("new_deal_vin_car")
            photo_car = data.get("new_deal_photo_car")

            if not all([deal_id, buyer_name, march_car, vin_code, photo_car]):
                await callback.answer("Не все данные заполнены, попробуйте с начала!")
                return

            existing_deal_id = await session.execute(
                select(Deals).where(Deals.deal_id == deal_id)
            )
            if existing_deal_id.scalar():
                await callback.answer(f"Такая сделка № {deal_id} уже существует в БД")
                return
            new_deal = Deals(
                deal_id=deal_id,
                buy_user = buyer_name,
                march_model=march_car,
                vin_code=vin_code,
                car_photo_id=photo_car
            )
            session.add(new_deal)
            await session.commit()

            await callback.answer(f"Новая сделка {deal_id} добавлена в БД")
            await callback.message.edit_reply_markup(
                inline_message_id=callback.inline_message_id,
                reply_markup=None)
            await state.clear()
            await bot.send_message(
                chat_id=callback.message.chat.id,
                text="ПАНЕЛЬ АДМИНИСТРАТОРА",
                reply_markup=kb_admin_main
            )

        except Exception as e:
            await session.rollback()
            logging.error(f"Ошибка при добавлении Сделки: {e}", exc_info=True)
            await callback.answer("Произошла ошибка при добавлении", show_alert=True)
