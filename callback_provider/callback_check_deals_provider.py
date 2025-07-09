from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals

callback_check_deals_provider_router = Router()

@callback_check_deals_provider_router.callback_query(F.data == "check_deals_provider")
async def check_deals_provider(callback: CallbackQuery):
    async with deals_session() as session:
        deals = await session.execute(
            select(Deals).where(Deals.provider_id == callback.from_user.id)
        )
        deals = deals.scalars().all()
        if deals:
            builder = InlineKeyboardBuilder()
            for deal in deals:
                builder.button(text=f"{deal.deal_id} {deal.buy_user}",
                               callback_data=f"check_deal_{deal.deal_id}")
            builder.button(text="Вернуться в меню", callback_data="back_to_main_menu_provider")
            builder.adjust(1)
            await callback.message.edit_text(text="Выберете сделку:",
                                             reply_markup=builder.as_markup())