import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User

callback_feedback_buyer_router = Router()

@callback_feedback_buyer_router.callback_query(F.data == "feedback_buyer")
async def feedback_buyer(callback: CallbackQuery, state: FSMContext):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
            await state.update_data(deal_id=deal_id)
    await callback.answer(text="Напишите Ваши впечатления одним текстом", show_alert=True)
    await callback.message.answer(text="Напишите Ваши впечатления одним текстом:")
    await state.set_state(Buyer.waiting_for_feedback_buyer)


@callback_feedback_buyer_router.message(Buyer.waiting_for_feedback_buyer)
async def feedback_buyer_text(message: Message, state: FSMContext):

    if not message.text:
        await message.answer("Напишите Ваши впечатления одним текстом:")
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Верно", callback_data="feedback_buyer_ok")
    builder.button(text="🚫 Написать Заново", callback_data="delete_message")
    await state.update_data(feedback_text=message.text)
    await message.answer(text=f"Вы написали:"
                              f"\n\n{message.text}\n\n"
                              f"Верно?",
                         reply_markup=builder.as_markup())

@callback_feedback_buyer_router.callback_query(F.data == "feedback_buyer_ok")
async def feedback_buyer_ok(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    deal_id = data['deal_id']
    feedback_text = data['feedback_text']
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer("Сделка не найдена")
            return
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
                        caption=f"️📝 Покупатель написал отзыв по сделке\n\n"
                                f"{message_text}\n\n"
                                f"📝ОТЗЫВ:\n{feedback_text}\n\n"
                    )
            await callback.message.delete_reply_markup()
            await state.clear()
    except Exception as e:
        logging.error(f"Error in add_questionnaire_to_db: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)
