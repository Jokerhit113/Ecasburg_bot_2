from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals

callback_transaction_actions_router = Router()

@callback_transaction_actions_router.callback_query(F.data == "transaction_actions")
async def transaction_actions(callback: CallbackQuery):
    lines = callback.message.caption.strip().split('\n')
    for line in lines:
        if line.startswith("Сделка №: "):
            deal_id = line.split('№: ')[-1].strip()
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()

    if not deal.contract_photo_id and not deal.contract_docs_id:
        add_contract_btn = "⚠️"  # Нет ни фото, ни видео
    else:
        add_contract_btn = "✅"  # Есть хотя бы что-то из этого

    if not deal.buyer_id:
        change_buyer_btn = "⚠️"  # Нет ни фото, ни видео
    else:
        change_buyer_btn = "✅"  # Есть хотя бы что-то из этого

    if not deal.provider_id:
        change_provider_btn = "⚠️"  # Нет ни фото, ни видео
    else:
        change_provider_btn = "✅"  # Есть хотя бы что-то из этого

    if not deal.broker_id:
        change_broker_btn = "⚠️"  # Нет ни фото, ни видео
    else:
        change_broker_btn = "✅"  # Есть хотя бы что-то из этого

    if not deal.carrier_id:
        change_carrier_btn = "⚠️"  # Нет ни фото, ни видео
    else:
        change_carrier_btn = "✅"  # Есть хотя бы что-то из этого

    if not deal.additional_options:
        add_additional_options_btn = "⚠️"  # Нет ни фото, ни видео
    else:
        add_additional_options_btn = "✅"  # Есть хотя бы что-то из этого

    if not deal.photo_docs_car_carrier and deal.docs_docs_car_carrier:
        already_for_issue = "❌"  # Нет ни фото, ни видео
    else:
        already_for_issue = "✅"  # Есть хотя бы что-то из этого


    builder = InlineKeyboardBuilder()
    builder.button(text=f"{add_contract_btn} Загрузить договор", callback_data="add_contract")
    builder.button(text=f"{change_buyer_btn} Выбрать покупателя", callback_data="change_buyer")
    builder.button(text=f"{change_provider_btn} Выбрать Поставщика", callback_data="change_provider")
    builder.button(text=f"{change_broker_btn} Выбрать Брокера", callback_data="change_broker")
    builder.button(text=f"{change_carrier_btn} Выбрать Логиста", callback_data="change_carrier")
    builder.button(text=f"{add_additional_options_btn} Добавить Доп. опции", callback_data="add_additional_options")
    builder.button(text=f"{already_for_issue} Готов к Выдаче", callback_data="car_is_ready_for_delivery")
    builder.button(text=f"🏁 Завершить Заказ", callback_data="end_deal_admin")
    builder.button(text="🚫 Удалить Заказ", callback_data="delete_deal")
    builder.button(text="⬅️ Назад в Меню", callback_data=f"deal_detail_{deal.id}")
    builder.adjust(1)
    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())


@callback_transaction_actions_router.callback_query(F.data == "delete_deal")
async def callback_get_deals_delete(callback: CallbackQuery):
    caption = callback.message.caption
    deal_id = caption.split('\n')[0].split('ID: ')[1]
    print(deal_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить", callback_data=f"delete_deal_{deal_id}")  # Теперь передаем user_id
    builder.button(text="⬅️ Назад", callback_data="transaction_actions")
    builder.adjust(1)
    await callback.message.edit_reply_markup(inline_message_id=callback.inline_message_id,
                                             reply_markup=builder.as_markup())