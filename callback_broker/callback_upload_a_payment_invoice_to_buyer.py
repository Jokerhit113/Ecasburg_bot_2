import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.orm import defer

from core.state_fsm import Broker, Buyer
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_upload_a_payment_invoice_to_buyer_router = Router()


@callback_upload_a_payment_invoice_to_buyer_router.callback_query(F.data == "upload_a_payment_invoice_to_buyer")
async def upload_a_payment_invoice_to_buyer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Брокер Выбрал загрузить счёт на оплату таможни по сделке {deal_id}")
    await state.update_data(deal_id=deal_id)
    await callback.answer()
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Файл", callback_data=f"upload_a_payment_invoice_to_buyer_document")
    builder.button(text="📝 Текст", callback_data=f"upload_a_payment_invoice_to_buyer_text")

    builder.button(text="⬅️ Назад в Меню", callback_data=f"list_broker_check_deal_{deal_id}")
    builder.adjust(2)
    await callback.message.answer(text="Выберете способ отправки реквизитов для оплаты:",
                                  reply_markup=builder.as_markup())


@callback_upload_a_payment_invoice_to_buyer_router.callback_query(F.data == "upload_a_payment_invoice_to_buyer_text")
async def upload_a_payment_invoice_to_buyer_text(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    deal_id = data['deal_id']
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Брокер Выбрал загрузить счёт файлом по сделке {deal_id}")
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад в Меню", callback_data=f"list_broker_check_deal_{deal_id}")
    await callback.message.edit_text("Напишите одним сообщением реквизиты и сумму к оплате:",
                                     reply_markup=builder.as_markup())
    await state.set_state(Broker.waiting_for_payment_invoice_to_buyer_text)

@callback_upload_a_payment_invoice_to_buyer_router.message(Broker.waiting_for_payment_invoice_to_buyer_text)
async def waiting_for_payment_invoice_to_buyer_text(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

    data = await state.get_data()
    deal_id = data['deal_id']
    await state.update_data(message_invoice=message.text)
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Всё верно", callback_data="invoice_ok")
        builder.button(text="❌ Написать снова", callback_data="delete_message")
        message_text = (
            f"Сделка №: {deal.deal_id}\n"
            f"Покупатель: {deal.buy_user}\n"
            f"Автомобиль: {deal.march_model}\n"
            f"VIN: {deal.vin_code}\n"
        )

        await message.answer(text=f"{message_text}\n\n"
                                  f"Реквизиты для оплаты Таможни:\n\n"
                                  f"{message.text}\n",
                             reply_markup=builder.as_markup())

@callback_upload_a_payment_invoice_to_buyer_router.callback_query(F.data == "invoice_ok")
async def invoice_ok(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    deal_id = data['deal_id']
    message_invoice = data['message_invoice']
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Брокер Подтвердил отправку счёта по сделке {deal_id}")
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        deal.payment_invoice_to_buyer_text = message_invoice
        await session.commit()
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить оплату", callback_data="accept_payment_invoice_to_buyer")
        message_text = (
            f"Сделка №: {deal.deal_id}\n"
            f"Покупатель: {deal.buy_user}\n"
            f"Автомобиль: {deal.march_model}\n"
            f"VIN: {deal.vin_code}\n"
        )
        await bot.send_photo(photo=deal.car_photo_id,
            chat_id=deal.buyer_id,
            caption=f"{message_text}\n\n"
                 f"Реквизиты для оплаты Таможни:\n\n"
                 f"{message_invoice}\n",
            reply_markup=builder.as_markup())

        await callback.message.edit_text(text=f"{callback.message.text}\n\n"
                                              f"📍 Реквизиты на оплату отправлены Покупателю, ожидайте подтверждение оплаты.")
        await state.clear()


@callback_upload_a_payment_invoice_to_buyer_router.callback_query(F.data == "upload_a_payment_invoice_to_buyer_document")
async def upload_a_payment_invoice_to_buyer_document(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    deal_id = data['deal_id']
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель Выбрал загрузить квитанцию по сделке {deal_id}")
    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад в Меню", callback_data=f"list_broker_check_deal_{deal_id}")
        builder.adjust(1)

        await callback.message.delete()
        await callback.message.answer(
            text="Загрузите Скан счёта на оплату для Покупателя:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(Broker.waiting_for_payment_invoice_to_buyer)
        await callback.answer()

    except Exception as e:
        logging.error(f"Error in upload_a_payment_invoice_to_buyer: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)


@callback_upload_a_payment_invoice_to_buyer_router.message(Broker.waiting_for_payment_invoice_to_buyer)
async def get_payment_invoice_to_buyer(message: Message, state: FSMContext, bot: Bot):
    await message.forward(chat_id=CHAT_LOG)

    data = await state.get_data()
    deal_id = data['deal_id']

    if not message.document:
        await message.answer("Отправьте Файл скан счёта на оплату")
        return

    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()

        if not deal:
            await message.answer("❌ Сделка не найдена")
            return

        deal.payment_invoice_to_buyer = message.document.file_id
        await session.commit()
        message_text = (
            f"Сделка №: {deal.deal_id}\n"
            f"Покупатель: {deal.buy_user}\n"
            f"Автомобиль: {deal.march_model}\n"
            f"VIN: {deal.vin_code}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить оплату", callback_data="accept_payment_invoice_to_buyer")

        await bot.send_document(
            chat_id=deal.buyer_id,
            document=deal.payment_invoice_to_buyer,
            caption=f"{message_text}\n\n"
                    f"Счёт на оплату от Брокера",
            reply_markup=builder.as_markup()
        )

        await message.answer("Счёт на оплату загружен и отправлен Покупателю, ожидайте подтверждение оплаты.")

@callback_upload_a_payment_invoice_to_buyer_router.callback_query(F.data == "accept_payment_invoice_to_buyer")
async def accept_payment_invoice_to_buyer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал оплатить счёт по Таможне по сделке {deal_id}")
    await state.update_data(deal_id=deal_id)
    await callback.message.delete_reply_markup()
    await callback.answer("Загрузите квитанцию об оплате", show_alert=True)
    await callback.message.answer("Загрузите документ с подтверждением оплаты")
    await state.set_state(Buyer.waiting_for_upload_payment_document_invoice_to_buyer)

@callback_upload_a_payment_invoice_to_buyer_router.message(Buyer.waiting_for_upload_payment_document_invoice_to_buyer)
async def upload_payment_document_invoice_to_buyer(message: Message, state: FSMContext, bot: Bot):
    await message.forward(chat_id=CHAT_LOG)

    data = await state.get_data()
    deal_id = data['deal_id']
    if not message.document:
        await message.answer("Отправьте Файл подтверждения оплаты")
        return
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await message.answer("Сделка не найдена")
            return
        deal.payment_document_invoice_to_buyer = message.document.file_id
        await session.commit()

        message_text = (
            f"Сделка №: {deal.deal_id}\n"
            f"Покупатель: {deal.buy_user}\n"
            f"Автомобиль: {deal.march_model}\n"
            f"VIN: {deal.vin_code}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Подтвердить получение оплаты", callback_data="accept_payment_document_invoice_to_buyer")

        await bot.send_document(
            chat_id=deal.broker_id,
            document=deal.payment_document_invoice_to_buyer,
            caption=f"{message_text}\n\n"
                    f"Квитанция об оплате счёта",
            reply_markup=builder.as_markup()

        )
        await message.answer("Квитанция об оплате счёта отправлена Брокеру ✅\n\n"
                             "Ожидайте подтверждения от Брокера")
        await state.clear()

@callback_upload_a_payment_invoice_to_buyer_router.callback_query(F.data == "accept_payment_document_invoice_to_buyer")
async def accept_payment_document_invoice_to_buyer(callback: CallbackQuery, bot: Bot):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer("Сделка не найдена")
            return
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name} Брокер подтвердил оплату счёта по сделке {deal_id}")
        deal.payment_document_invoice_to_buyer_yes_no = "Оплата по счёту получена"
        message_text = (
            f"Сделка №: {deal.deal_id}\n"
            f"Покупатель: {deal.buy_user}\n"
            f"Автомобиль: {deal.march_model}\n"
            f"VIN: {deal.vin_code}\n"
        )
        await bot.send_message(
            chat_id=deal.buyer_id,
            text=f"{message_text}\n\n"
                 f"Оплата счёта подтверждена Брокером ✅")
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n"
                    f"Оплата подтверждена ✅",
        reply_markup=None)


