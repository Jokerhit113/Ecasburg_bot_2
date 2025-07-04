from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User


callback_change_provider_router = Router()

async def get_all_providers(session: AsyncSession):
    result = await session.execute(select(User).where(User.departament == "provider"))
    return result.scalars().all()


@callback_change_provider_router.callback_query(F.data == "change_provider")
async def change_provider(callback: CallbackQuery):
    async with user_session() as session:
        providers = await get_all_providers(session)

        if not providers:
            await callback.answer("В Базе нет Поставщиков")
            return
        builder = InlineKeyboardBuilder()

        for provider in providers:
            builder.button(
                text=f"{provider.name}",
                callback_data=f"provider_{provider.id}",
            )
        builder.button(text="Назад к списку сделок", callback_data="admin_all_orders_list")
        builder.adjust(1)
        await callback.message.edit_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=builder.as_markup()
        )

@callback_change_provider_router.callback_query(F.data.startswith("provider_"))
async def change_provider_add(callback: CallbackQuery):
    async with user_session() as session:
        provider_data = await session.execute(select(User).where(User.id == callback.data.split("_")[-1]))
        provider_data_ = provider_data.scalar_one_or_none()
        provider = callback.data.split("_")[1]
        builder = InlineKeyboardBuilder()
        builder.button(text=f"Добавить к сделке", callback_data=f"add_provider_{provider}")
        builder.button(text="Назад к списку сделок", callback_data="admin_all_orders_list")
        builder.adjust(1)
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}"
                    f"\n\nВы хотите добавить к сделке Поставщика:\n\n"
                 f"{provider_data_.name}",
            reply_markup=builder.as_markup()
        )


@callback_change_provider_router.callback_query(F.data.startswith("add_provider_"))
async def change_provider_add_to_deal(callback: CallbackQuery):
    async with user_session() as session_user:
        # Получаем данные поставщика
        result_user = await session_user.execute(
            select(User).where(User.id == callback.data.split("_")[-1])
        )
        provider = result_user.scalar_one_or_none()

        if not provider:
            await callback.answer("Поставщик не найден", show_alert=True)
            return

        provider_id_tg = provider.user_id

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

            deal.provider_id = provider_id_tg
            await session_deals.commit()
            builder = InlineKeyboardBuilder()
            builder.button(text="◀ Назад к списку", callback_data="admin_all_orders_list")
            builder.adjust(1)
            # Обновляем текст сообщения
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n"
                        f"Поставщик: {provider.name}\n"
                        f"ID_TG: {provider_id_tg}\n"
                        f"Добавлен к сделке.",
                reply_markup=builder.as_markup()
            )
            await callback.answer("Поставщик успешно добавлен")