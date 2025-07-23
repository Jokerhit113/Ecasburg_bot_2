from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User
from settings import CHAT_LOG

callback_change_broker_router = Router()

async def get_all_broker(session: AsyncSession):
    result = await session.execute(select(User).where(User.departament == "broker"))
    return result.scalars().all()


@callback_change_broker_router.callback_query(F.data == "change_broker")
async def change_broker(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал: Выбрать Брокера")
    async with user_session() as session:
        brokers = await get_all_broker(session)

        if not brokers:
            await callback.answer("В Базе нет Брокеров>")
            return
        builder = InlineKeyboardBuilder()

        for broker in brokers:
            builder.button(
                text=f"{broker.name}",
                callback_data=f"broker_{broker.id}",
            )
        builder.button(text="⬅️ Назад к списку сделок", callback_data="admin_all_orders_list")
        builder.adjust(1)
        await callback.message.edit_reply_markup(
            inline_message_id=callback.inline_message_id,
            reply_markup=builder.as_markup()
        )

@callback_change_broker_router.callback_query(F.data.startswith("broker_"))
async def change_broker_add(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал Брокера {callback.data}")
    async with user_session() as session:
        broker_data = await session.execute(select(User).where(User.id == callback.data.split("_")[-1]))
        broker_data_ = broker_data.scalar_one_or_none()
        broker = callback.data.split("_")[1]
        builder = InlineKeyboardBuilder()
        builder.button(text=f"Добавить к сделке", callback_data=f"add_broker_{broker}")
        builder.button(text="⬅️ Назад к списку сделок", callback_data="admin_all_orders_list")
        builder.adjust(1)
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}"
                    f"\n\nВы хотите добавить к сделке Брокера:\n\n"
                 f"{broker_data_.name}",
            reply_markup=builder.as_markup()
        )


@callback_change_broker_router.callback_query(F.data.startswith("add_broker_"))
async def change_broker_add_to_deal(callback: CallbackQuery, bot: Bot):

    async with user_session() as session_user:
        # Получаем данные поставщика
        result_user = await session_user.execute(
            select(User).where(User.id == callback.data.split("_")[-1])
        )
        broker = result_user.scalar_one_or_none()

        if not broker:
            await callback.answer("Брокер не найден", show_alert=True)
            return

        broker_id_tg = broker.user_id

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

            deal.broker_id = broker_id_tg
            await session_deals.commit()
            builder = InlineKeyboardBuilder()
            builder.button(text="⬅️ Назад к списку", callback_data="admin_all_orders_list")
            builder.adjust(1)
            # Обновляем текст сообщения
            await callback.message.edit_caption(
                caption=f"{callback.message.caption}\n\n"
                        f"Брокер: {broker.name}\n"
                        f"ID_TG: {broker_id_tg}\n"
                        f"Добавлен к сделке.",
                reply_markup=builder.as_markup()
            )
            await bot.send_message(chat_id=CHAT_LOG,
                                   text=f"{callback.from_user.first_name} {callback.from_user.last_name} Добавил брокера {broker.name}, к сделке {deal.deal_id}")
            await callback.answer("Брокер успешно добавлен")