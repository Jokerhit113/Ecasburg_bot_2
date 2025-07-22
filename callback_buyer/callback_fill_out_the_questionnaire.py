import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals
from data_base.db_users import User, user_session

callback_fill_out_the_questionnaire_router = Router()

text = ("Для заполнения анкеты понадобятся следующие данные: \n"
        "- номер телефона\n"
        "- Адрес Фактического проживания\n"
        "- Электронная почта\n"
        "- был ли ввоз авто в течение 1 Года из других стран\n"
        "- информация о наличии авто в личном пользовании (если есть, надо указать марку/модель и год выпуска авто)")

@callback_fill_out_the_questionnaire_router.callback_query(F.data == "fill_out_the_questionnaire")
async def fill_out_the_questionnaire(callback: CallbackQuery, state: FSMContext):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Ваша Сделка №: ')[1])
    await state.update_data(deal_id=deal_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в Меню", callback_data=f"deal_list_buyer_{deal_id}")
    builder.adjust(1)
    await callback.message.edit_caption(caption=text,
                                      reply_markup=builder.as_markup())
    await callback.message.answer(text="Напишите Ваш номер телефона:\n\n"
                                             "Например: 89123456789")
    await state.set_state(Buyer.waiting_phone_number_buyer)

@callback_fill_out_the_questionnaire_router.message(Buyer.waiting_phone_number_buyer)
async def get_phone_number_buyer(message: Message, state: FSMContext):
    await state.update_data(phone_number = message.text)
    await message.answer("Напишите Ваш Адрес Фактического проживания:\n\n"
                         "Например: г. Екатеринбург, ул. Амундсена, д. 45, кв. 132")
    await state.set_state(Buyer.waiting_for_actual_address_of_residence)

@callback_fill_out_the_questionnaire_router.message(Buyer.waiting_for_actual_address_of_residence)
async def get_actual_address_of_residence(message: Message, state: FSMContext):
    await state.update_data(actual_address_of_residence = message.text)
    await message.answer("Напишите Ваш E-Mail:\n\n"
                         "Например: info@e-carsburg.ru")
    await state.set_state(Buyer.waiting_for_email_address)

@callback_fill_out_the_questionnaire_router.message(Buyer.waiting_for_email_address)
async def get_actual_address_of_residence(message: Message, state: FSMContext):
    await state.update_data(email_address = message.text)
    reply_builder = ReplyKeyboardBuilder()
    reply_builder.add(KeyboardButton(text="ДА"))
    reply_builder.add(KeyboardButton(text="НЕТ"))
    reply_markup = reply_builder.as_markup(resize_keyboard=True)
    await message.answer(
        text="Был ли ввоз авто в течение Года из других стран\n\n"
                         "Выбирите ДА / НЕТ",
        reply_markup=reply_markup
    )
    await state.set_state(Buyer.waiting_for_imported_yes_no)

@callback_fill_out_the_questionnaire_router.message(Buyer.waiting_for_imported_yes_no)
async def get_imported_yes_no(message: Message, state: FSMContext):
    await state.update_data(imported_yes_no = message.text)
    await message.answer(
        text="Напишите информацию о наличии авто в личном пользовании (если есть, надо указать марку/модель и год выпуска авто)\n\n"
                         "Например: Toyota Rav 4, 2010 г\n\n"
                         "Если нет авто в личном пользовании то напишите: НЕТ",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Buyer.waiting_for_have_car)

@callback_fill_out_the_questionnaire_router.message(Buyer.waiting_for_have_car)
async def get_have_car(message: Message, state: FSMContext):
    await state.update_data(have_car = message.text)
    data = await state.get_data()
    phone_number = data['phone_number']
    actual_address_of_residence = data['actual_address_of_residence']
    email_address = data['email_address']
    imported_yes_no = data['imported_yes_no']
    have_car = data['have_car']
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Всё верно", callback_data="add_questionnaire_to_db")
    builder.button(text="❌ Заполнить Заново", callback_data="back_main_buyer")
    builder.adjust(1)
    await message.answer(text=f"Вы заполнили данные:\n\n"
                         f"Ваш номер телефона: {phone_number}\n"
                         f"Ваш фактический адрес проживания: {actual_address_of_residence}\n"
                         f"Ваш E-mail адрес: {email_address}\n"
                         f"Был ли ввоз авто за последний ГОД: {imported_yes_no}\n"
                         f"Автомобиль в данные момент: {have_car}\n",
                         reply_markup=builder.as_markup())

@callback_fill_out_the_questionnaire_router.callback_query(F.data == "add_questionnaire_to_db")
async def add_questionnaire_to_db(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    deal_id = data.get('deal_id')
    phone_number = data['phone_number']
    actual_address_of_residence = data['actual_address_of_residence']
    email_address = data['email_address']
    imported_yes_no = data['imported_yes_no']
    have_car = data['have_car']
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if deal:
            deal.buyer_phone_number = phone_number
            deal.buyer_actual_address_of_residence = actual_address_of_residence
            deal.buyer_email_address = email_address
            deal.buyer_imported_yes_no = imported_yes_no
            deal.buyer_have_car = have_car
            await session.commit()
            if imported_yes_no == "ДА":
                try:
                    async with user_session() as u_session:
                        users = await u_session.execute(
                            select(User).where(User.departament == "admin")
                        )
                        users = users.scalars().all()
                        if users:
                            message_text = (
                                f"Сделка №: {deal.deal_id}\n"
                                f"Покупатель: {deal.buy_user}\n"
                                f"Автомобиль: {deal.march_model}\n"
                                f"VIN: {deal.vin_code}\n"
                                f"Номер телефона: {deal.buyer_phone_number}"
                            )
                            for user in users:
                                await bot.send_photo(
                                    chat_id=user.user_id,
                                    photo=deal.car_photo_id,
                                    caption=f"️‼️‼️‼️‼️‼️‼️‼️‼️‼️\n\n"
                                            f"{message_text}\n\n"
                                            f"‼️ У Клиента был ввоз автомобиля из-за границы за последний ГОД!"
                                )
                except Exception as e:
                    logging.error(f"Error in add_questionnaire_to_db: {e}")
                    await callback.answer("Произошла ошибка", show_alert=True)


            builder = InlineKeyboardBuilder()
            builder.button(text="⬅️ Назад к списку Сделок", callback_data="check_deals_buyer")
            builder.adjust(1)
            await callback.answer(text="Все данные успешно сохранены в базе данных")
            await callback.message.edit_text(text="Все данные успешно сохранены в базе данных",
                                             reply_markup=builder.as_markup())
        else:
            await callback.answer("Сделка не найдена")

    await state.clear()