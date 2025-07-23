import logging
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_buyer_main
from settings import CHAT_LOG

callback_payment_confirmation_buyer_router = Router()


@callback_payment_confirmation_buyer_router.callback_query(F.data == "payment_confirmation_buyer")
async def payment_confirmation_buyer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал: Загрузить Квитанцию об оплате автомобиля")
    """Обработчик начала процесса подтверждения оплаты"""
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Ваша Сделка №: ')[1])
    await state.update_data(deal_id=deal_id)
    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data=f"deal_list_buyer_{deal_id}")
        builder.adjust(1)

        await callback.message.edit_caption(
            caption="Загрузите Фото/Скан подтверждения оплаты:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(Buyer.waiting_for_payment)
        await callback.answer()

    except Exception as e:
        logging.error(f"Error in payment_confirmation_buyer: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)


@callback_payment_confirmation_buyer_router.message(Buyer.waiting_for_payment)
async def payment_confirmation_buyer_get_photo(message: Message, state: FSMContext, bot: Bot):
    await message.forward(chat_id=CHAT_LOG)

    """Обработчик получения подтверждения оплаты"""
    try:
        data = await state.get_data()
        deal_id = data.get('deal_id')
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
                select(Deals).where(Deals.deal_id == deal_id)
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

            try:
                builder = InlineKeyboardBuilder()
                builder.button(text="✅ Деньги получены!", callback_data="confirmation_payment_buyer_provider")
                if message.photo:
                    media_group = [
                        InputMediaPhoto(media=message.photo[-1].file_id),
                        InputMediaPhoto(media=deal.car_photo_id)
                    ]
                    await bot.send_media_group(
                        chat_id=deal.provider_id,
                        media=media_group
                    )

                elif message.document:
                    await bot.send_photo(
                        chat_id=deal.provider_id,
                        photo=deal.car_photo_id
                    )
                    await bot.send_document(
                        chat_id=deal.provider_id,
                        document=message.document.file_id,
                    )


                await bot.send_message(
                    chat_id=deal.provider_id,
                    text=f"Сделка №: {deal.deal_id}\n"
                            f"Покупатель: {deal.buy_user}\n"
                            f"Автомобиль: {deal.march_model}\n"
                            f"VIN: {deal.vin_code}\n\n"
                            f"Подтвердите получение денежных средств.",
                    reply_markup=builder.as_markup())
            except Exception as e:
                logging.error(f"Error in forward message for provider {e}", exc_info=True)
                await message.answer("Поставщик ещё не назначен")
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