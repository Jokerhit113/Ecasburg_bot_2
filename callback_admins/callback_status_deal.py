import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User

callback_status_deal_router = Router()


@callback_status_deal_router.callback_query(F.data == "check_status")
async def callback_get_deals_check_status(callback: CallbackQuery):
    try:
        # Получаем ID сделки из сообщения
        caption = callback.message.caption or ""
        deal_id = caption.split('\n')[0].split('ID: ')[1]

        async with deals_session() as session:
            # Получаем сделку
            deal = await session.get(Deals, deal_id)
            if not deal:
                await callback.answer("Сделка не найдена", show_alert=True)
                return

            async with user_session() as session_user:
                # Получаем всех участников сделки одним запросом
                user_ids = [
                    deal.buyer_id,
                    deal.provider_id,
                    deal.broker_id,
                    deal.carrier_id
                ]

                users = await session_user.execute(
                    select(User).where(User.user_id.in_(user_ids))
                )
                users = {user.user_id: user for user in users.scalars()}

                # Создаем клавиатуру
                builder = InlineKeyboardBuilder()
                buttons = [
                    ("Чек об оплате", "payment_check"),
                    ("Фото/Видео Выкупа авто", "purchase_media"),
                    ("Доставка до ТК на Границу", "delivery_to_border"),
                    ("Документы на авто от Поставщика", "provider_docs"),
                    ("Назад к Списку", "admin_all_orders_list")
                ]

                for text, callback_data in buttons:
                    builder.button(text=text, callback_data=callback_data)

                builder.adjust(1)  # Все кнопки в отдельных рядах

                # Формируем текст сообщения
                caption_text = (
                    f"ID: {deal.id}\n"
                    f"Данные по сделке:\n\n"
                    f"Сделка №: {deal.deal_id}\n"
                    f"Покупатель: {users.get(deal.buyer_id, User(name='Не указан')).name}\n"
                    f"Покупатель tg_id: {deal.buyer_id}\n"
                    f"Автомобиль: {deal.march_model}\n"
                    f"Vin code: {deal.vin_code}\n"
                    f"Поставщик: {users.get(deal.provider_id, User(name='Не указан')).name}\n"
                    f"Брокер: {users.get(deal.broker_id, User(name='Не указан')).name}\n"
                    f"Перевозчик: {users.get(deal.carrier_id, User(name='Не указан')).name}\n"
                )

                await callback.message.edit_caption(
                    caption=caption_text,
                    reply_markup=builder.as_markup()
                )

    except IndexError:
        await callback.answer("Ошибка: неверный формат сообщения", show_alert=True)
    except Exception as e:
        logging.error(f"Error in check_status: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обработке запроса", show_alert=True)

@callback_status_deal_router.callback_query(F.data == "delete_deal")
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
