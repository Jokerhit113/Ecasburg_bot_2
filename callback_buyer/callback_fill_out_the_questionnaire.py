

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals

callback_fill_out_the_questionnaire_router = Router()

text = ("Для заполнения анкеты понадобятся следующие данные: \n"

        "- номер телефона\n"
        "- Адрес Фактического проживания\n"
        "- Электронная почта\n"
        "- Наличие в/у (номер, серия)\n"
        "- был ли ввоз авто в течение 3 последних лет из других стран\n"
        "- информация о наличии авто в личном пользовании (если есть, надо указать марку/модель и год выпуска авто)")

@callback_fill_out_the_questionnaire_router.callback_query(F.data == "fill_out_the_questionnaire")
async def fill_out_the_questionnaire(callback_query: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад", callback_data="add_documents_buyer")
    builder.adjust(1)
    await callback_query.message.edit_text(text=text,
                                      reply_markup=builder.as_markup())
    await callback_query.message.answer(text="Напишите Ваш номер телефона:\n\n"
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
    await message.answer("Если у Вас есть Водительское удостоверение, то напишите номер и серию ВУ\n\n"
                         "Например: 99 17 134546\n\n"
                         "Если ВУ нет, то напишите Нет ВУ")
    await state.set_state(Buyer.waiting_for_driver_license)

@callback_fill_out_the_questionnaire_router.message(Buyer.waiting_for_driver_license)
async def get_driver_license(message: Message, state: FSMContext):
    await state.update_data(driver_license = message.text)
    await message.answer("Был ли ввоз авто в течение 3 последних лет из других стран\n\n"
                         "Напишите ДА / НЕТ")
    await state.set_state(Buyer.waiting_for_imported_yes_no)

@callback_fill_out_the_questionnaire_router.message(Buyer.waiting_for_imported_yes_no)
async def get_imported_yes_no(message: Message, state: FSMContext):
    await state.update_data(imported_yes_no = message.text)
    await message.answer("Напишите информацию о наличии авто в личном пользовании (если есть, надо указать марку/модель и год выпуска авто)\n\n"
                         "Например: Toyota Rav 4, 2010 г\n\n"
                         "Если нет авто в личном пользовании то напишите: НЕТ")
    await state.set_state(Buyer.waiting_for_have_car)

@callback_fill_out_the_questionnaire_router.message(Buyer.waiting_for_have_car)
async def get_have_car(message: Message, state: FSMContext):
    await state.update_data(have_car = message.text)
    data = await state.get_data()
    phone_number = data['phone_number']
    actual_address_of_residence = data['actual_address_of_residence']
    email_address = data['email_address']
    driver_license = data['driver_license']
    imported_yes_no = data['imported_yes_no']
    have_car = data['have_car']
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Всё верно", callback_data="add_questionnaire_to_db")
    builder.button(text="❌ Заполнить Заново", callback_data="fill_out_the_questionnaire")
    builder.button(text="Назад в меню", callback_data="back_main_buyer")
    builder.adjust(1)
    await message.answer(text=f"Вы заполнили данные:\n\n"
                         f"Ваш номер телефона: {phone_number}\n"
                         f"Ваш фактический адрес проживания: {actual_address_of_residence}\n"
                         f"Ваш E-mail адрес: {email_address}\n"
                         f"Водительское удостоверение: {driver_license}\n"
                         f"Был ли ввоз авто за последние 3 года: {imported_yes_no}\n"
                         f"Автомобиль в данные момент: {have_car}\n",
                         reply_markup=builder.as_markup())

@callback_fill_out_the_questionnaire_router.callback_query(F.data == "add_questionnaire_to_db")
async def add_questionnaire_to_db(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    phone_number = data['phone_number']
    actual_address_of_residence = data['actual_address_of_residence']
    email_address = data['email_address']
    driver_license = data['driver_license']
    imported_yes_no = data['imported_yes_no']
    have_car = data['have_car']
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.buyer_id == callback.from_user.id)
        )
        deal = deal.scalar_one_or_none()
        if deal:
            deal.buyer_phone_number = phone_number
            deal.buyer_actual_address_of_residence = actual_address_of_residence
            deal.buyer_email_address = email_address
            deal.buyer_driver_license = driver_license
            deal.buyer_imported_yes_no = imported_yes_no
            deal.buyer_have_car = have_car
            await session.commit()
            builder = InlineKeyboardBuilder()
            builder.button(text="Назад к списку документов", callback_data="add_documents_buyer")
            builder.adjust(1)
            await callback.answer(text="Все данные успешно сохранены в базе данных")
            await callback.message.edit_text(text="Все данные успешно сохранены в базе данных",
                                             reply_markup=builder.as_markup())
        else:
            await callback.answer("Сделка не найдена")

    await state.clear()