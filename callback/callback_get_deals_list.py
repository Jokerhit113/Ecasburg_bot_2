import re

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_deals import deals_session, Deals
from keyboard.admins_inline_keyboard import kb_deal

callback_get_deals_list_router = Router()

async def get_all_deals(session: AsyncSession):
    result = await session.execute(select(Deals))
    return result.scalars().all()

@callback_get_deals_list_router.callback_query(F.data == "admin_all_orders")
async def callback_get_deals_list(callback: CallbackQuery):
    async with deals_session() as session:
        deals = await get_all_deals(session)

        if not deals:
            await callback.answer("В базе нет Сделок", show_alert=True)
            return

        builder = InlineKeyboardBuilder()

        for deal in deals:
            builder.button(
                text=f"{deal.deal_id} {deal.buy_user}",
                callback_data=f"deal_detail_{deal.id}",
            )
        builder.button(text="Назад в меню", callback_data="back_to_menu")
        builder.adjust(1)

        await callback.message.edit_text(
            text="СПИСОК СДЕЛОК:",
            reply_markup=builder.as_markup()
        )


@callback_get_deals_list_router.callback_query(F.data.startswith("deal_detail_"))
async def callback_get_deals_switch(callback: CallbackQuery):
    async with deals_session() as session:
        deal_id = int(callback.data.split("_")[-1])
        deal = await session.get(Deals, deal_id)

        if not deal:
            await callback.answer("Сделка не найдена", show_alert=True)
            return
        await callback.message.answer_photo(
            photo=deal.car_photo_id,
            caption=f"ID: {deal.id}\n"
                    f"Сделка № {deal.deal_id}\n"
                    f"Покупатель: {deal.buy_user}\n"
                    f"Автомобиль: {deal.march_model}\n"
                    f"Vin code: {deal.vin_code}\n",
            reply_markup=kb_deal
        )
        await callback.message.delete()

@callback_get_deals_list_router.callback_query(F.data == "admin_all_orders_list")
async def callback_get_deals_list(callback: CallbackQuery):
    async with deals_session() as session:
        deals = await get_all_deals(session)

        if not deals:
            await callback.answer("В базе нет Сделок", show_alert=True)
            return

        builder = InlineKeyboardBuilder()

        for deal in deals:
            builder.button(
                text=f"{deal.deal_id} {deal.buy_user}",
                callback_data=f"deal_detail_{deal.id}"
            )
        builder.button(text="Назад в меню", callback_data="back_to_menu")
        builder.adjust(1)
        await callback.message.delete()

        await callback.message.answer(
            text="СПИСОК СДЕЛОК:",
            reply_markup=builder.as_markup()
        )

@callback_get_deals_list_router.callback_query(F.data == "check_status")
async def callback_get_deals_check_status(callback: CallbackQuery):
    async with deals_session() as session:
        caption = callback.message.caption
        deal_id = caption.split('\n')[0].split('ID: ')[1]
        deal = await session.get(Deals, deal_id)
        if not deal:
            await callback.answer("Сделка не найдена", show_alert=True)
            return
        builder = InlineKeyboardBuilder()
        builder.button(text="Чек об оплате", callback_data="1")
        builder.button(text="Фото/Видео Выкупа авто", callback_data="1")
        builder.button(text="Доставка до ТК на Границу", callback_data="1")
        builder.button(text="Документы на авто от Поставщика", callback_data="1")
        builder.button(text="Кнопка", callback_data="1")
        builder.button(text="Кнопка", callback_data="1")
        builder.button(text="Кнопка", callback_data="1")
        builder.button(text="Кнопка", callback_data="1")
        builder.button(text="Кнопка", callback_data="1")
        builder.button(text="Назад к Списку", callback_data="admin_all_orders_list")

        builder.adjust(1)
        await callback.message.edit_caption(caption = f"ID: {deal.id}\n"
                                                      f"Данные по сделке:\n\n"
                                                      f"Покупатель: {deal.buy_user}\n"
                                                      f"Автомобиль: {deal.march_model}\n"
                                                      f"Vin code: {deal.vin_code}\n"
                                                      f"Поставщик: {deal.provider_id}\n"
                                                      f"Брокер: {deal.broker_id}\n"
                                                      f"Перевозчик: {deal.carrier_id}\n",
                                            reply_markup=builder.as_markup())

@callback_get_deals_list_router.callback_query(F.data == "delete_deal")
async def callback_get_deals_delete(callback: CallbackQuery):
    caption = callback.message.caption
    deal_id = caption.split('\n')[0].split('ID: ')[1]
    print(deal_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"delete_deal_{deal_id}")  # Теперь передаем user_id
    builder.button(text="◀ Назад", callback_data="admin_all_orders_list")
    builder.adjust(1)
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id,
                                             reply_markup=builder.as_markup())


@callback_get_deals_list_router.callback_query(F.data.startswith("delete_deal_"))
async def callback_get_deals_confirm_delete(callback: CallbackQuery):
    async with deals_session() as session:
        result = await session.execute(select(Deals).where(Deals.id == callback.data.split("_")[-1]))
        deal = result.scalar_one_or_none()
        if deal:
            await session.delete(deal)
            await session.commit()
            await callback.answer("Сделка Удалена!", show_alert=True)
            await callback.message.delete()
        else:
            await callback.answer("Ошибка при удалении сделки.", show_alert=True)
