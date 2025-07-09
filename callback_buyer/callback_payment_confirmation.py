import logging
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import NewDeals, Buyer
from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_back_to_menu, kb_admin_main, kb_buyer_main

callback_payment_confirmation_buyer_router = Router()


@callback_payment_confirmation_buyer_router.callback_query(F.data == "payment_confirmation_buyer")
async def payment_confirmation_buyer(callback: CallbackQuery, state: FSMContext):
    """Обработчик начала процесса подтверждения оплаты"""
    try:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="Назад в Меню",
            callback_data="back_main_buyer"
        )
        builder.adjust(1)

        await callback.message.edit_text(
            text="Загрузите Фото/Скан подтверждения оплаты:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(Buyer.waiting_for_payment)
        await callback.answer()

    except Exception as e:
        logging.error(f"Error in payment_confirmation_buyer: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)


@callback_payment_confirmation_buyer_router.message(Buyer.waiting_for_payment)
async def payment_confirmation_buyer_get_photo(message: Message, state: FSMContext, bot: Bot):
    """Обработчик получения подтверждения оплаты"""
    try:
        # Проверяем тип содержимого
        if not (message.photo or message.document):
            await message.answer("Пожалуйста, отправьте фото или документ с подтверждением оплаты")
            return

        # Сохраняем файл в состояние
        file_id = message.photo[-1].file_id if message.photo else message.document.file_id
        await state.update_data(payment_file_id=file_id)

        async with deals_session() as session:
            # Ищем сделку по user_id покупателя
            deal = await session.execute(
                select(Deals).where(Deals.buyer_id == message.from_user.id)
            )
            deal = deal.scalar_one_or_none()

            if not deal:
                await message.answer("❌ Сделка не найдена")
                return

            # Обновляем данные о платеже
            if message.photo:
                deal.payment_photo_id = file_id
            elif message.document:
                deal.payment_document_id = file_id
            else:
                await message.answer("Пожалуйста, отправьте фото или документ с подтверждением оплаты")

            await session.commit()

            # Отправляем подтверждение
            builder = InlineKeyboardBuilder()
            builder.button(text="В главное меню", callback_data="back_main_buyer")

            await message.answer(
                "✅ Чек об оплате принят!\n"
                "Ожидайте подтверждения от поставщика",
                reply_markup=builder.as_markup()
            )
            await state.clear()

            # Можно добавить уведомление администратору/поставщику
            # await notify_provider(bot, deal.id, message.from_user.id)

    except Exception as e:
        logging.error(f"Error in payment_confirmation_buyer_get_photo: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при обработке платежа")



@callback_payment_confirmation_buyer_router.callback_query(F.data == "back_main_buyer")
async def back_main_buyer(callback: CallbackQuery):
    await callback.message.answer(text=f"Добро пожаловать в панель Заказчика, благодарим Вас за выбор E-CarsBurg",
                         reply_markup=kb_buyer_main)
    await callback.message.delete()