import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy import select
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_confirmation_payment_buyer_provider_router = Router()

@callback_confirmation_payment_buyer_provider_router.callback_query(F.data == "confirmation_payment_buyer_provider")
async def confirmation_payment_buyer_provider(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Поставщик Подтвердил оплату автомобиля Покупателем")
    try:
        caption = callback.message.text
        deal_id = caption.split('\n')[0].split('Сделка №: ')[1]

        async with deals_session() as session:
            deal = await session.execute(
                select(Deals).where(Deals.deal_id == deal_id)
            )
            deal = deal.scalar_one_or_none()
            if not deal:
                await callback.answer("The transaction was not found")
                return
            await bot.send_message(chat_id=CHAT_LOG,
                                   text=f"{callback.from_user.first_name} {callback.from_user.last_name} Поставщик Подтвердил оплату автомобиля Покупателем по сделке {deal_id}")
            deal.payment_confirmation_yes_no = "Деньги получены поставщиком"
            await session.commit()

            await bot.send_message(chat_id = deal.buyer_id, text="Поставщик подтвердил получение денежных средств ✅")
            await callback.answer("The notification has been sent to the Buyer! ✅")
            await callback.message.delete_reply_markup()
            await callback.message.edit_text(text=f"{callback.message.text}\n\n"
                                                  f"Confirmation has been sent! ✅")

    except Exception as e:
        logging.error(f"Error in confirmation_payment_buyer_provider: {e}", exc_info=True)
        await callback.answer("Произошла ошибка")