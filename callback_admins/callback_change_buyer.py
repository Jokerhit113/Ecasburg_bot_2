from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User


callback_change_buyer_router = Router()

async def get_all_buyer(session: AsyncSession):
    result = await session.execute(select(User).where(User.departament == "buyer"))
    return result.scalars().all()


@callback_change_buyer_router.callback_query(F.data == "change_buyer")
async def change_buyer(callback: CallbackQuery):
    async with user_session() as session:
        buyers = await get_all_buyer(session)

        if not buyers:
            await callback.answer("В Базе нет Покупателей")
            return
        builder = InlineKeyboardBuilder()

        for buyer in buyers:
            builder.button(
                text=f"{buyer.name}",
                callback_data=f"buyer_{buyer.id}",
            )
        builder.button(text="Назад к списку сделок", callback_data="admin_all_orders_list")
        builder.adjust(1)
        await callback.message.edit_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=builder.as_markup()
        )

@callback_change_buyer_router.callback_query(F.data.startswith("buyer_"))
async def change_buyer_add(callback: CallbackQuery):
    async with user_session() as session:
        buyer_data = await session.execute(select(User).where(User.id == callback.data.split("_")[-1]))
        buyer_data_ = buyer_data.scalar_one_or_none()
        buyer = callback.data.split("_")[1]
        builder = InlineKeyboardBuilder()
        builder.button(text=f"Добавить к сделке", callback_data=f"add_buyer_{buyer}")
        builder.button(text="Назад к списку сделок", callback_data="admin_all_orders_list")
        builder.adjust(1)
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}"
                    f"\n\nВы хотите добавить к сделке Покупателя:\n\n"
                 f"{buyer_data_.name}",
            reply_markup=builder.as_markup()
        )


@callback_change_buyer_router.callback_query(F.data.startswith("add_buyer_"))
async def change_buyer_add_to_deal(callback: CallbackQuery):
    async with user_session() as session_user:
        # Получаем данные поставщика
        result_user = await session_user.execute(
            select(User).where(User.id == callback.data.split("_")[-1])
        )
        buyer = result_user.scalar_one_or_none()

        if not buyer:
            await callback.answer("Покупатель не найден", show_alert=True)
            return

        buyer_id_tg = buyer.user_id

        # Извлекаем ID сделки из текста сообщения
        try:
            caption = callback.message.caption
            deal_id = int(caption.split('\n')[0].split('ID: ')[1])
        except (IndexError, ValueError):
            await callback.answer("Не удалось определить ID сделки", show_alert=True)
            return

        async with deals_session() as session_deals:
            # Находим сделку и обновляем поставщика
            deal = await session_deals.get(Deals, deal_id)
            if not deal:
                await callback.answer("Сделка не найдена", show_alert=True)
                return

            deal.buyer_id = buyer_id_tg
            await session_deals.commit()

            # Обновляем текст сообщения
            builder = InlineKeyboardBuilder()
            builder.button(text="◀ Назад к списку", callback_data="admin_all_orders_list")
            builder.adjust(1)
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n"
                        f"Покупатель: {buyer.name}\n"
                        f"ID_TG: {buyer_id_tg}\n"
                        f"Добавлен к сделке.",
                reply_markup=builder.as_markup()
            )
            await callback.answer("Покупатель успешно добавлен")