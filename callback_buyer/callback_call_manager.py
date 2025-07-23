from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User
from settings import CHAT_LOG

callback_call_manager_router = Router()

@callback_call_manager_router.callback_query(F.data == "call_manager")
async def call_manager(callback: CallbackQuery, state: FSMContext):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Ваша Сделка №: ')[1])
    await state.update_data(deal_id=deal_id)
    await callback.message.answer(
        text="Напишите Ваш вопрос и менеджер свяжется с Вами в ближайшее время:"
    )
    await callback.answer(text="Напишите Ваш вопрос и менеджер свяжется с Вами в ближайшее время", show_alert=True)
    await state.set_state(Buyer.waiting_for_question_call)

@callback_call_manager_router.message(Buyer.waiting_for_question_call)
async def waiting_for_question_call(message: Message, state: FSMContext, bot: Bot):
    await message.forward(chat_id=CHAT_LOG)

    data = await state.get_data()
    deal_id = data.get("deal_id")

    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()

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
                        caption=f"️‼️ Запрос Покупателя на Обратный звонок\n\n"
                                f"{message_text}\n\n"
                                f"Вопрос клиента:\n\n"
                                f"{message.text}"
                    )

        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data=f"deal_list_buyer_{deal_id}")
        await message.answer(
            text="Ваш запрос отправлен, Менеджер свяжется с Вами в ближайшее время",
        reply_markup=builder.as_markup())
        await state.clear()