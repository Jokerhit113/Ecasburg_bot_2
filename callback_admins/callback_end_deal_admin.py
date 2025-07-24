from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Admin
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_end_deal_admin_router = Router()


@callback_end_deal_admin_router.callback_query(F.data == "end_deal_admin")
async def end_deal_admin(callback: CallbackQuery, state: FSMContext, bot: Bot):

    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
            await state.update_data(deal_id=deal_id)
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        await state.update_data(deal_id=deal_id)
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал Завершить Сделку {deal_id}")
        if not deal:
            await callback.answer(text=f"Сделка №: {deal_id} не найдена", show_alert=True)
            return
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Завершить", callback_data=f"end_deal_admin_apply")
        builder.button(text="⬅️ Назад", callback_data=f"transaction_actions")
        builder.adjust(1)

        await callback.message.edit_reply_markup(reply_markup=builder.as_markup())


@callback_end_deal_admin_router.callback_query(F.data == "end_deal_admin_apply")
async def end_deal_admin_apply(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал Подтвердил Завершить Сделку")
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=f"end_deal_admin")
    builder.adjust(1)

    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())
    await callback.message.answer(
        text="Загрузите Фото Передачи Автомобиля Клиенту:"
    )
    await state.set_state(Admin.waiting_for_transfer_photo_car)

@callback_end_deal_admin_router.message(Admin.waiting_for_transfer_photo_car)
async def end_deal_admin_photo(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

    if not message.photo:
        await message.answer("Отправьте фото выдачи автомобиля покупателю")
        return
    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()
    deal_id = data["deal_id"]
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
    builder.button(text="✅ Завершить", callback_data=f"finally_end_deal_admin_apply")
    builder.button(text="Удалить фото", callback_data=f"delete_message")
    builder.adjust(1)
    await message.answer_photo(
        photo=message.photo[-1].file_id,
        caption=f"{message_text}\n\n"
                f"ЗАВЕРШИТЬ СДЕЛКУ❓",
        reply_markup=builder.as_markup()
    )

@callback_end_deal_admin_router.callback_query(F.data == "finally_end_deal_admin_apply")
async def finally_end_deal_admin_apply(callback: CallbackQuery, state: FSMContext, bot: Bot):

    data = await state.get_data()
    deal_id = data["deal_id"]
    photo = data["photo"]
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()

        if not deal:
            await callback.answer(text="Сделка не найдена")
            return
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name}  Завершил Сделку {deal_id}")
        deal.finally_photo = photo
        await session.commit()
        await callback.message.delete()
        message_text = (
            f"Сделка №: {deal.deal_id}\n"
            f"Покупатель: {deal.buy_user}\n"
            f"Автомобиль: {deal.march_model}\n"
            f"VIN: {deal.vin_code}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="Главное Меню", callback_data=f"back_to_menu")
        await callback.message.answer(f"{message_text}\n\n"
                                      f"✅ Все пользователи сделки отвязаны от неё, "
                                      f"но она сохранена в БД, в любой момент Вы можете посмотреть всю информацию "
                                      f"по этой сделке пока не удалите её через меню \n\n"
                                      f"ДЕЙСТВИЯ СО СДЕЛКОЙ -> УДАЛИТЬ ЗАКАЗ",
                                      reply_markup=builder.as_markup())
        builder2 = InlineKeyboardBuilder()
        builder2.button(text="❤️ ОСТАВИТЬ ОТЗЫВ", callback_data="feedback_buyer")
        await bot.send_photo(
            chat_id=deal.buyer_id,
            photo=photo,
            caption=f"{message_text}\n\n"
                    f"{deal.buy_user}! Надеемся, ваш {deal.march_model} уже приносит Вам радость за рулём! 🌟\n\n"  
                    "Для нас важно, чтобы каждый клиент оставался доволен. Если у вас есть пара минут, поделитесь, "
                    "пожалуйста, впечатлениями о нашей работе: что нам стоит улучшить или что понравилось особенно?\n\n"  
                    "Нам важен любой отзыв — даже пара слов. 💬\n"
                    "Заранее спасибо за честность! Ваше мнение поможет нам делать сервис ещё удобнее.\n\n" 
                    "Хороших дорог!\n"
                    "С Уважением команда E-CarsBurg 😎",
            reply_markup=builder2.as_markup()
        )
        deal.buyer_id = ""
        deal.provider_id = ""
        deal.broker_id = ""
        deal.carrier_id = ""
        await session.commit()
        await state.clear()
