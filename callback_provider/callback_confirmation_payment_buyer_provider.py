import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy import select
from data_base.db_deals import deals_session, Deals

callback_confirmation_payment_buyer_provider_router = Router()

@callback_confirmation_payment_buyer_provider_router.callback_query(F.data == "confirmation_payment_buyer_provider")
async def confirmation_payment_buyer_provider(callback: CallbackQuery, bot: Bot):
    try:
        caption = callback.message.text
        deal_id = int(caption.split('\n')[0].split('Сделка №: ')[1])

        async with deals_session() as session:
            deal = await session.execute(
                select(Deals).where(Deals.deal_id == deal_id)
            )
            deal = deal.scalar_one_or_none()
            deal.payment_confirmation_yes_no = "Деньги получены поставщиком"
            await session.commit()

            await bot.send_message(chat_id = deal.buyer_id, text="Поставщик подтвердил получение денежных средств ✅")
            await callback.answer("Уведомление Покупателю отправлено! ✅")
            await callback.message.delete_reply_markup()
            await callback.message.edit_text(text=f"{callback.message.text}\n\n"
                                                  f"Подтверждение отправлено! ✅")

    except Exception as e:
        logging.error(f"Error in confirmation_payment_buyer_provider: {e}", exc_info=True)
        await callback.answer("Произошла ошибка")