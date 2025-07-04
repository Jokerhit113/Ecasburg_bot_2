from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User


callback_change_carrier_router = Router()

async def get_all_carrier(session: AsyncSession):
    result = await session.execute(select(User).where(User.departament == "carrier"))
    return result.scalars().all()


@callback_change_carrier_router.callback_query(F.data == "change_carrier")
async def change_carrier(callback: CallbackQuery):
    async with user_session() as session:
        carriers = await get_all_carrier(session)

        if not carriers:
            await callback.answer("В Базе нет Брокеров>")
            return
        builder = InlineKeyboardBuilder()

        for carrier in carriers:
            builder.button(
                text=f"{carrier.name}",
                callback_data=f"carrier_{carrier.id}",
            )
        builder.button(text="Назад к списку сделок", callback_data="admin_all_orders_list")
        builder.adjust(1)
        await callback.message.edit_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=builder.as_markup()
        )

@callback_change_carrier_router.callback_query(F.data.startswith("carrier_"))
async def change_carrier_add(callback: CallbackQuery):
    async with user_session() as session:
        carrier_data = await session.execute(select(User).where(User.id == callback.data.split("_")[-1]))
        carrier_data_ = carrier_data.scalar_one_or_none()
        carrier = callback.data.split("_")[1]
        builder = InlineKeyboardBuilder()
        builder.button(text=f"Добавить к сделке", callback_data=f"add_carrier_{carrier}")
        builder.button(text="Назад к списку сделок", callback_data="admin_all_orders_list")
        builder.adjust(1)
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}"
                    f"\n\nВы хотите добавить к сделке Поставщика:\n\n"
                 f"{carrier_data_.name}",
            reply_markup=builder.as_markup()
        )


@callback_change_carrier_router.callback_query(F.data.startswith("add_carrier_"))
async def change_carrier_add_to_deal(callback: CallbackQuery):
    async with user_session() as session_user:
        # Получаем данные поставщика
        result_user = await session_user.execute(
            select(User).where(User.id == callback.data.split("_")[-1])
        )
        carrier = result_user.scalar_one_or_none()

        if not carrier:
            await callback.answer("Брокер не найден", show_alert=True)
            return

        carrier_id_tg = carrier.user_id

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

            deal.carrier_id = carrier_id_tg
            await session_deals.commit()

            # Обновляем текст сообщения
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n"
                        f"Поставщик: {carrier.name}\n"
                        f"ID_TG: {carrier_id_tg}\n"
                        f"Добавлен к сделке."
            )
            await callback.answer("Поставщик успешно добавлен")