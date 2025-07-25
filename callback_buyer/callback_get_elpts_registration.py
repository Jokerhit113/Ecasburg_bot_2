import logging
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.state_fsm import NewDeals, Buyer
from data_base.db_deals import deals_session, Deals
from keyboard.inline_keyboard import kb_buyer_main
from settings import CHAT_LOG

callback_get_elpts_registration_router = Router()


@callback_get_elpts_registration_router.callback_query(F.data == "get_elpts_registration")
async def get_elpts_registration_buyer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал: Загрузить Фото регистрации на портале ЭПТС")
    """Обработчик начала процесса подтверждения оплаты"""
    caption = callback.message.caption
    deal_id = caption.split('\n')[0].split('Ваша Сделка №: ')[1]
    await state.update_data(deal_id=deal_id)
    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Назад в Меню", callback_data=f"deal_list_buyer_{deal_id}")
        builder.adjust(1)

        await callback.message.edit_caption(
            caption="Загрузите Фото Скрин с сайта ЭПТС:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(Buyer.waiting_for_get_registration_elpts)
        await callback.answer()

    except Exception as e:
        logging.error(f"Error in get_elpts_registration: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)


@callback_get_elpts_registration_router.message(Buyer.waiting_for_get_registration_elpts)
async def get_elpts_registration_buyer_get_photo(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)

    """Обработчик получения подтверждения оплаты"""
    data = await state.get_data()
    deal_id = data.get('deal_id')
    try:
        # Проверяем тип содержимого
        if not message.photo:
            await message.answer("Пожалуйста, отправьте Скрин с сайта ЭПТС")
            return

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
                deal.elpts_registration_photo = message.photo[-1].file_id

            await session.commit()

            # Отправляем подтверждение
            builder = InlineKeyboardBuilder()
            builder.button(text="⬅️ Назад", callback_data=f"deal_list_buyer_{deal_id}")

            await message.answer(
                "✅ Скрин принят!\n",
                reply_markup=builder.as_markup()
            )
            await state.clear()

    except Exception as e:
        logging.error(f"Error in payment_confirmation_buyer_get_photo: {e}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при загрузке скрина")

