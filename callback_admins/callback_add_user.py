from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_users import User, user_session
from core.state_fsm import NewUser

import logging

from keyboard.inline_keyboard import kb_admin_main
from settings import CHAT_LOG

callback_add_user_router = Router()


@callback_add_user_router.callback_query(F.data == "add_new_user")
async def add_new_user_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
        text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал: Добавить пользователя")
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


@callback_add_user_router.callback_query(NewUser.waiting_for_departament)
async def get_departament(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
        text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал: Департамент {callback.data}")
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


@callback_add_user_router.message(NewUser.waiting_for_name)
async def get_name_new_user(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)
    await state.update_data(name=message.text)
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отменить", callback_data="cancel_add_user")
    await message.answer(
        text="Напишите ID Пользователя Телеграмм (только цифры):",
        reply_markup=builder.as_markup()
    )
    await state.set_state(NewUser.waiting_for_user_id)


@callback_add_user_router.message(NewUser.waiting_for_user_id)
async def get_id_new_user(message: Message, state: FSMContext):
    await message.forward(chat_id=CHAT_LOG)
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


@callback_add_user_router.callback_query(F.data == "add_new_user_to_db_users")
async def add_new_user_to_db_users(callback: CallbackQuery, state: FSMContext, bot: Bot):
    async with user_session() as session:
        try:
            data = await state.get_data()
            name_get = data.get('name')
            user_id_get = data.get('user_id')
            departament_get = data.get('departament')

            if not all([user_id_get, name_get, departament_get]):
                await callback.answer("Не все данные заполнены", show_alert=True)
                return
            await bot.send_message(chat_id=CHAT_LOG,
                                   text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал: Добавил пользователя: {name_get}, {user_id_get}, {departament_get}")

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


@callback_add_user_router.callback_query(F.data == "cancel_add_user")
async def cancel_adding_user(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
        text=f"{callback.from_user.first_name} {callback.from_user.last_name} выбрал: Отменить добавление пользователя")
    await state.clear()
    await callback.message.edit_text(text=f"ПАНЕЛЬ АДМИНИСТРАТОРА", reply_markup=kb_admin_main)
    await callback.answer("Вы вернулись в меню администратора")

