import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Admin
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User
from settings import CHAT_LOG

callback_car_is_ready_for_delivery_router = Router()

@callback_car_is_ready_for_delivery_router.callback_query(F.data == "car_is_ready_for_delivery")
async def end_deal_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):

    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        await state.update_data(deal_id=deal_id)
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал: Автомобиль готов к выдаче {deal.deal_id}, {deal.buy_user}")

    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data=f"deal_detail_{deal.id}")
        builder.adjust(1)

        await callback.message.edit_caption(
            caption="Загрузите Фото Готового к выдаче автомобиля:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(Admin.waiting_for_ready_for_issue_car)
        await callback.answer()

    except Exception as e:
        logging.error(f"Error in payment_confirmation_buyer: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)

@callback_car_is_ready_for_delivery_router.message(Admin.waiting_for_ready_for_issue_car)
async def waiting_for_ready_for_issue_car(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

    data = await state.get_data()
    deal_id = data["deal_id"]
    await state.update_data(photo=message.photo[-1].file_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ ОТПРАВИТЬ", callback_data=f"send_ready_for_issue_car")
    builder.button(text="⬅️ Назад", callback_data=f"deal_detail_{deal_id}")
    builder.adjust(1)

    await message.answer_photo(
        photo=message.photo[-1].file_id,
        caption=f"👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩\n\n"
                    f"Ваш Автомобиль ГОТОВ к ВЫДАЧЕ!!!✅\n\n"
                    f"👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩",
        reply_markup=builder.as_markup()
    )

@callback_car_is_ready_for_delivery_router.callback_query(F.data == "send_ready_for_issue_car")
async def send_ready_for_issue_car(callback: CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    deal_id = data["deal_id"]
    photo = data["photo"]
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал: Уведомить Покупателя о готовности выдачи авто {deal_id}")
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return

        deal.car_is_ready_for_delivery = photo

        await session.commit()

        message_text = (
            f"Сделка №: {deal.deal_id}\n"
            f"Покупатель: {deal.buy_user}\n"
            f"Автомобиль: {deal.march_model}\n"
            f"VIN: {deal.vin_code}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="🎉 УРА 🎉", callback_data=f"congratulation")
        builder.adjust(1)
        await bot.send_photo(
            chat_id=deal.buyer_id,
            photo=photo,
            caption=f"{message_text}\n\n"
                    f"👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩\n\n"
                    f"{deal.buy_user} Ваш Автомобиль ГОТОВ к ВЫДАЧЕ!!!✅\n\n"
                    f"👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩👏🎉🎈🥳🤩",
            reply_markup=builder.as_markup()

        )
        await callback.answer(f"{deal.buy_user} ПОЛУЧИЛ УВЕДОМЛЕНИЕ!!!", show_alert=True)
        await callback.message.delete()
        await state.clear()

@callback_car_is_ready_for_delivery_router.callback_query(F.data == "congratulation")
async def congratulation(callback: CallbackQuery, bot: Bot):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name} Получил уведомление о готовности авто {deal.march_model} к выдаче")

    await callback.message.answer("🥳")
    await callback.message.answer("🎉")
    await callback.message.answer("🤩")
    await callback.message.answer("🎈")
    await callback.message.answer("👏")
    await callback.message.delete_reply_markup()
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
                        photo=deal.car_is_ready_for_delivery,
                        caption=f"️✅✅✅✅✅️✅✅✅✅\n\n"
                                f"{message_text}\n\n"
                                f"✅ Клиент ОЧЕНЬ РАД что Автомобиль готов к выдаче! ✅"
                    )
    except Exception as e:
        logging.error(f"Error in add_questionnaire_to_db: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

