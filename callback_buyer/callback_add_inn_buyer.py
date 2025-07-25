import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from core.state_fsm import Buyer
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_add_inn_buyer_router = Router()

@callback_add_inn_buyer_router.callback_query(F.data == "upload_inn_buyer")
async def inn_buyer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал: Загрузить ИНН")
    """Обработчик начала процесса подтверждения оплаты"""
    caption = callback.message.caption
    deal_id = caption.split('\n')[0].split('Ваша Сделка №: ')[1]
    await state.update_data(deal_id=deal_id)
    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад", callback_data=f"deal_list_buyer_{deal_id}")
        builder.adjust(1)

        await callback.message.edit_caption(
            caption="Загрузите Скан или фото ИНН:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(Buyer.waiting_for_upload_inn)
        await callback.answer()

    except Exception as e:
        logging.error(f"Error in upload_inn_buyer: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)


@callback_add_inn_buyer_router.message(Buyer.waiting_for_upload_inn)
async def upload_inn_buyer(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

    """Обработчик получения подтверждения оплаты"""
    data = await state.get_data()
    deal_id = data.get('deal_id')
    try:
        # Проверяем тип содержимого
        if not (message.photo or message.document):
            await message.answer("Пожалуйста, Отправьте Фото или Скан ИНН")
            return

        # Сохраняем файл в состояние

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
                deal.inn_photo = message.photo[-1].file_id
            elif message.document:
                deal.inn_docs = message.document.file_id

            await session.commit()

            # Отправляем подтверждение
            builder = InlineKeyboardBuilder()
            builder.button(text="⬅️ Назад", callback_data=f"deal_list_buyer_{deal_id}")

            await message.answer(
                "✅ ИНН принят!\n",
                reply_markup=builder.as_markup()
            )
            await state.clear()

    except Exception as e:
        logging.error(f"Error in payment_confirmation_buyer_get_photo: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при загрузке скрина")