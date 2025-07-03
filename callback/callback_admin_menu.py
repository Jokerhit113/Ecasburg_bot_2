from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_users import User, async_session
from core.state_fsm import NewUser

import logging

from keyboard.admins_inline_keyboard import kb_admin_main

callback_admin_router = Router()


@callback_admin_router.callback_query(F.data == "add_new_user")
async def add_new_user_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NewUser.waiting_for_departament)
    builder = InlineKeyboardBuilder()
    builder.button(text="Администратор", callback_data="admin")
    builder.button(text="Поставщик", callback_data="provider")
    builder.button(text="Брокер", callback_data="broker")
    builder.button(text="Перевозчик", callback_data="carrier")
    builder.button(text="Покупатель", callback_data="buyer")
    builder.button(text="❌ Отменить", callback_data="cancel_add_user")
    builder.adjust(1)

    await callback.message.edit_text(
        text="Кого хотите добавить?",
        reply_markup=builder.as_markup()
    )


@callback_admin_router.callback_query(NewUser.waiting_for_departament)
async def get_departament(callback: CallbackQuery, state: FSMContext):
    if callback.data == "cancel_add_user":
        await callback.message.edit_text(text=f"ПАНЕЛЬ АДМИНИСТРАТОРА", reply_markup=kb_admin_main)
        await callback.answer("Вы вернулись в меню администратора")
        await state.clear()
        return

    await state.update_data(departament=callback.data)
    await callback.message.edit_text(
        text="Укажите Имя Пользователя:",
        reply_markup=None
    )
    await state.set_state(NewUser.waiting_for_name)


@callback_admin_router.message(NewUser.waiting_for_name)
async def get_name_new_user(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отменить", callback_data="cancel_add_user")
    await message.answer(
        text="Напишите ID Пользователя Телеграмм (только цифры):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(NewUser.waiting_for_user_id)


@callback_admin_router.message(NewUser.waiting_for_user_id)
async def get_id_new_user(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        data = await state.get_data()

        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Добавить в БД", callback_data="add_new_user_to_db_users")
        builder.button(text="❌ Отменить", callback_data="cancel_add_user")
        builder.adjust(1)

        await message.answer(
            text="Вы хотите добавить пользователя:\n\n"
                 f"Имя: {data['name']}\n"
                 f"Департамент: {data['departament']}\n"
                 f"ID Пользователя: {user_id}",
            reply_markup=builder.as_markup()
        )
    except ValueError:
        await message.answer("ID должен быть числом! Попробуйте еще раз.")


@callback_admin_router.callback_query(F.data == "add_new_user_to_db_users")
async def add_new_user_to_db_users(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        try:
            data = await state.get_data()
            name_get = data.get('name')
            user_id_get = data.get('user_id')
            departament_get = data.get('departament')

            if not all([user_id_get, name_get, departament_get]):
                await callback.answer("Не все данные заполнены", show_alert=True)
                return

            existing_user = await session.execute(
                select(User).where(User.user_id == user_id_get)
            )
            if existing_user.scalar_one_or_none():
                await callback.answer(f"Пользователь с ID {user_id_get} уже существует", show_alert=True)
                return

            new_user = User(
                user_id=user_id_get,
                name=name_get,
                departament=departament_get
            )
            session.add(new_user)
            await session.commit()

            await callback.answer(f"Пользователь {name_get} успешно добавлен", show_alert=True)
            await callback.message.edit_text(
                f"✅ Новый пользователь добавлен:\n"
                f"ID: {user_id_get}\n"
                f"Имя: {name_get}\n"
                f"Отдел: {departament_get}"
            )
            await state.clear()
            await callback.message.edit_text(text=f"ПАНЕЛЬ АДМИНИСТРАТОРА", reply_markup=kb_admin_main)
            await callback.answer("Вы вернулись в меню администратора")

        except Exception as e:
            await session.rollback()
            logging.error(f"Ошибка при добавлении пользователя: {e}", exc_info=True)
            await callback.answer("Произошла ошибка при добавлении", show_alert=True)


@callback_admin_router.callback_query(F.data == "cancel_add_user")
async def cancel_adding_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(text=f"ПАНЕЛЬ АДМИНИСТРАТОРА", reply_markup=kb_admin_main)
    await callback.answer("Вы вернулись в меню администратора")

async def get_all_users(session: AsyncSession):
    result = await session.execute(select(User))
    return result.scalars().all()


@callback_admin_router.callback_query(F.data == "show_all_users")
async def show_all_users(callback: CallbackQuery):
    async with async_session() as session:
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

        builder.button(text="❌ Закрыть", callback_data="close_users_list")
        builder.adjust(1)  # По одной кнопке в ряд

        await callback.message.edit_text(
            "Список пользователей:",
            reply_markup=builder.as_markup()
        )


@callback_admin_router.callback_query(F.data == "close_users_list")
async def close_users_list(callback: CallbackQuery):
    await callback.message.edit_text(text=f"ПАНЕЛЬ АДМИНИСТРАТОРА", reply_markup=kb_admin_main)
    await callback.answer("Вы вернулись в меню администратора")


@callback_admin_router.callback_query(F.data.startswith("user_detail_"))
async def show_user_detail(callback: CallbackQuery):
    async with async_session() as session:
        user_id = int(callback.data.split("_")[-1])  # Это внутренний ID (первичный ключ)
        user = await session.get(User, user_id)

        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        builder = InlineKeyboardBuilder()
        builder.button(text="🗑 Удалить", callback_data=f"confirm_delete_{user.user_id}")  # Теперь передаем user_id
        builder.button(text="◀ Назад", callback_data="show_all_users")
        builder.adjust(1)

        await callback.message.edit_text(
            f"Детали пользователя:\n\n"
            f"ID: {user.id}\n"
            f"Имя: {user.name}\n"
            f"User ID: {user.user_id}\n"
            f"Отдел: {user.departament}",
            reply_markup=builder.as_markup()
        )


@callback_admin_router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_user(callback: CallbackQuery):
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


@callback_admin_router.callback_query(F.data.startswith("delete_user_"))
async def delete_user_handler(callback: CallbackQuery):
    async with async_session() as session:
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
@callback_admin_router.callback_query(F.data.startswith("user_detail_by_tgid_"))
async def show_user_detail_by_tgid(callback: CallbackQuery):
    async with async_session() as session:
        tg_user_id = int(callback.data.split("_")[-1])

        result = await session.execute(select(User).where(User.user_id == tg_user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        # Возвращаем к стандартному view с внутренним ID
        await show_user_detail(callback, session)
