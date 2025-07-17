from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals

callback_request_check_docs_from_the_broker_router = Router()

@callback_request_check_docs_from_the_broker_router.callback_query(F.data == "request_check_docs_from_the_broker")
async def request_check_docs_from_the_broker(callback: CallbackQuery, state: FSMContext, bot: Bot):

    data = await state.get_data()
    payment_confirmation_buyer_btn = data.get("payment_confirmation_buyer_btn")
    add_passport_btn = data.get("add_passport_btn")
    driver_license_load_buyer_btn = data.get("driver_license_load_buyer_btn")
    add_snils_buyer_btn = data.get("add_snils_buyer_btn")
    foreign_currency_account_statement_btn = data.get("foreign_currency_account_statement_btn")
    cash_flow_statement_btn = data.get("cash_flow_statement_btn")
    fill_out_the_questionnaire_btn = data.get("fill_out_the_questionnaire_btn")
    get_elpts_registration_btn = data.get("get_elpts_registration_btn")
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Ваша Сделка №: ')[1])

    if payment_confirmation_buyer_btn and add_passport_btn and driver_license_load_buyer_btn and add_snils_buyer_btn and foreign_currency_account_statement_btn and cash_flow_statement_btn and fill_out_the_questionnaire_btn and get_elpts_registration_btn == "✅":
        async with deals_session() as session:
            deal = await session.execute(
                select(Deals).where(Deals.deal_id == deal_id)
            )
            deal = deal.scalar_one_or_none()
            message_text = (
                f"Сделка №: {deal.deal_id}\n"
                f"Покупатель: {deal.buy_user}\n"
                f"Автомобиль: {deal.march_model}\n"
                f"VIN: {deal.vin_code}\n"
            )
            builder = InlineKeyboardBuilder()
            builder.button(text="🔍 Проверить документы", callback_data="check_the_buyer_documents")
            await bot.send_photo(
                chat_id=deal.broker_id,
                photo=deal.car_photo_id,
                caption=f"{message_text}\n\n"
                        f"⚠️ Покупатель загрузил все документы, ожидает подтверждения проверки документов",
                reply_markup=builder.as_markup()
            )
            await callback.answer()
            await callback.message.answer("Запрос Брокеру на проверку документов Отправлен ✅\n"
                                          "Ожидайте подтверждения приёма документов.")
    else:
        await callback.answer(
            text="Вы загрузили не все документы, все пункты меню должны быть ✅",
            show_alert=True)
        return