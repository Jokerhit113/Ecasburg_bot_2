from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_users import User, user_session
from settings import CHAT_LOG

callback_delete_user_router = Router()

async def get_all_users(session: AsyncSession):
    result = await session.execute(select(User))
    return result.scalars().all()


@callback_delete_user_router.callback_query(F.data == "show_all_users")
async def show_all_users(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал Удалить пользователя")
    async with user_session() as session:
        users = await get_all_users(session)

        if not users:
            await callback.answer("В базе нет пользователей", show_alert=True)
            return

        builder = InlineKeyboardBuilder()

        # Добавляем кнопки для каждого пользователя
        for user in users:
            builder.button(
                text=f"{user.name} ({user.departament})",
                callback_data=f"user_detail_{user.id}"
            )

        builder.button(text="❌ Закрыть", callback_data="back_to_menu")
        builder.adjust(1)  # По одной кнопке в ряд

        await callback.message.edit_text(
            "Список пользователей:",
            reply_markup=builder.as_markup()
        )


@callback_delete_user_router.callback_query(F.data.startswith("user_detail_"))
async def show_user_detail(callback: CallbackQuery, bot: Bot):
    async with user_session() as session:
        user_id = int(callback.data.split("_")[-1])  # Это внутренний ID (первичный ключ)
        user = await session.get(User, user_id)

        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        builder = InlineKeyboardBuilder()
        builder.button(text="🗑 Удалить", callback_data=f"confirm_delete_{user.user_id}")  # Теперь передаем user_id
        builder.button(text="⬅️ Назад", callback_data="show_all_users")
        builder.adjust(1)

        await callback.message.edit_text(
            f"Детали пользователя:\n\n"
            f"ID: {user.id}\n"
            f"Имя: {user.name}\n"
            f"User ID: {user.user_id}\n"
            f"Отдел: {user.departament}",
            reply_markup=builder.as_markup()
        )
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал Удалить пользователя {user.name}")


@callback_delete_user_router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_user(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал Подтвердил удаление пользователя")
    tg_user_id = int(callback.data.split("_")[-1])  # Получаем user_id (не id)

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"delete_user_{tg_user_id}")
    builder.button(text="❌ Нет, отменить", callback_data=f"user_detail_by_tgid_{tg_user_id}")
    builder.adjust(1)

    await callback.message.edit_text(
        "Вы уверены, что хотите удалить этого пользователя?",
        reply_markup=builder.as_markup()
    )

# Добавьте эту функцию в начало (перед хэндлерами)
async def delete_user_by_user_id(session: AsyncSession, tg_user_id: int):
    result = await session.execute(select(User).where(User.user_id == tg_user_id))
    user = result.scalar_one_or_none()
    if user:
        await session.delete(user)
        await session.commit()
        return True
    return False


@callback_delete_user_router.callback_query(F.data.startswith("delete_user_"))
async def delete_user_handler(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал Удалил пользователя {callback.data}")
    async with user_session() as session:
        tg_user_id = int(callback.data.split("_")[-1])

        success = await delete_user_by_user_id(session, tg_user_id)

        if success:
            builder = InlineKeyboardBuilder()
            builder.button(text="◀ К списку пользователей", callback_data="show_all_users")

            await callback.message.edit_text(
                f"✅ Пользователь с User ID {tg_user_id} успешно удален",
                reply_markup=builder.as_markup()
            )
        else:
            await callback.answer("Ошибка при удалении пользователя", show_alert=True)


# Новый хэндлер для возврата к деталям по user_id
@callback_delete_user_router.callback_query(F.data.startswith("user_detail_by_tgid_"))
async def show_user_detail_by_tgid(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал Отменить удаление пользователя")
    async with user_session() as session:
        tg_user_id = int(callback.data.split("_")[-1])

        result = await session.execute(select(User).where(User.user_id == tg_user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        # Возвращаем к стандартному view с внутренним ID
        await show_user_detail(callback, session)
