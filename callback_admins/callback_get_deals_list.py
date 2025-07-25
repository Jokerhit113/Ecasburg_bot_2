from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_get_deals_list_router = Router()

async def get_all_deals(session: AsyncSession):
    result = await session.execute(select(Deals))
    return result.scalars().all()

@callback_get_deals_list_router.callback_query(F.data == "admin_all_orders")
async def callback_get_deals_list(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Выбрал список всех сделок")
    async with deals_session() as session:
        deals = await get_all_deals(session)

        if not deals:
            await callback.answer("В базе нет Сделок", show_alert=True)
            return

        builder = InlineKeyboardBuilder()

        for deal in deals:
            if not deal.finally_photo:
                btn = "🟢"
            else:
                btn = "🏁"
            builder.button(
                text=f"{btn} {deal.deal_id} {deal.buy_user}",
                callback_data=f"deal_detail_{deal.id}",
            )
        builder.button(text="⬅️ Назад в меню", callback_data="back_to_menu")
        builder.adjust(1)

        await callback.message.edit_text(
            text="СПИСОК СДЕЛОК:",
            reply_markup=builder.as_markup()
        )


@callback_get_deals_list_router.callback_query(F.data.startswith("deal_detail_"))
async def callback_get_deals_switch(callback: CallbackQuery, bot: Bot):
    async with deals_session() as session:
        deal_id = callback.data.split("_")[-1]
        deal = await session.get(Deals, deal_id)

        if not deal:
            await callback.answer("Сделка не найдена", show_alert=True)
            return
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name} Выбрал сделку {deal.deal_id}")
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 Проверить статус", callback_data="check_status")
        builder.button(text="❕ Действия со сделкой", callback_data="transaction_actions")
        builder.button(text="⬅️ Назад к списку", callback_data="admin_all_orders_list")
        builder.adjust(1)

        await callback.message.answer_photo(
            photo=deal.car_photo_id,
            caption=f"ID: {deal.id}\n"
                    f"Сделка №: {deal.deal_id}\n"
                    f"Покупатель: {deal.buy_user}\n"
                    f"Автомобиль: {deal.march_model}\n"
                    f"Vin code: {deal.vin_code}\n"
                    f"Доп опции:\n {deal.additional_options}",
            reply_markup=builder.as_markup()
        )
        await callback.message.delete()

@callback_get_deals_list_router.callback_query(F.data == "admin_all_orders_list")
async def callback_get_deals_list(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Выбрал список всех сделок")
    async with deals_session() as session:
        deals = await get_all_deals(session)

        if not deals:
            await callback.answer("В базе нет Сделок", show_alert=True)
            return

        builder = InlineKeyboardBuilder()

        for deal in deals:
            if not deal.finally_photo:
                btn = "🟢"
            else:
                btn = "🏁"
            builder.button(
                text=f"{btn}{deal.deal_id} {deal.buy_user}",
                callback_data=f"deal_detail_{deal.id}"
            )
        builder.button(text="⬅️ Назад в меню", callback_data="back_to_menu")
        builder.adjust(1)
        await callback.message.delete()

        await callback.message.answer(
            text="СПИСОК СДЕЛОК:",
            reply_markup=builder.as_markup()
        )


@callback_get_deals_list_router.callback_query(F.data.startswith("delete_deal_"))
async def callback_get_deals_confirm_delete(callback: CallbackQuery, bot: Bot):
    async with deals_session() as session:
        result = await session.execute(select(Deals).where(Deals.id == callback.data.split("_")[-1]))
        deal = result.scalar_one_or_none()
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name} Выбрал удалить сделку {deal.deal_id}")
        if deal:
            await session.delete(deal)
            await session.commit()
            await callback.answer("Сделка Удалена!", show_alert=True)
            await callback.message.delete()
        else:
            await callback.answer("Ошибка при удалении сделки.", show_alert=True)
