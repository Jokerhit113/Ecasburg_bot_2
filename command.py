from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import Router, Bot
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from data_base.db_users import user_session, User
import logging
from keyboard.inline_keyboard import kb_admin_main, kb_buyer_main, kb_provider_main, kb_broker_main, kb_carrier_main
from settings import CHAT_LOG

router_command = Router()


async def get_departament_by_user_id(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(
        select(User.departament)
        .where(User.user_id == user_id)
    )
    departament = result.scalar_one_or_none()
    return departament


@router_command.message(Command("start"))
async def cmd_start(message: Message, bot: Bot):
    await bot.forward_message(
        chat_id=CHAT_LOG,
    from_chat_id=message.chat.id,
    message_id=message.message_id,
    )
    await bot.send_message(
        chat_id=CHAT_LOG,
        text=f"ID пользователя: {message.from_user.id}",
    )
    async with user_session() as session:
        try:
            # Ищем пользователя по user_id (не по id, если id и user_id разные)
            result = await session.execute(
                select(User)
                .where(User.user_id == message.from_user.id)
            )
            user = result.scalar_one_or_none()

            if not user:
                await message.answer(
                    "Вы не зарегистрированы в системе. Для регистрации обратитесь к администратору бота.")
                return

            # Получаем department (правильное написание)
            department = user.departament  # Прямой доступ к атрибуту

            if department == "admin":
                await message.answer(text=f"ПАНЕЛЬ АДМИНИСТРАТОРА", reply_markup=kb_admin_main)
            elif department == "buyer":
                await message.answer(text=f"Добро пожаловать в панель Покупателя, благодарим Вас за выбор E-CarsBurg",
                                     reply_markup=kb_buyer_main)
            elif department == "provider":
                await message.answer(text="Welcome to the partner menu of E-CarsBurg.\n\n"
                                          "Use the button below to get a list of your deals.",
                                     reply_markup=kb_provider_main)
            elif department == "broker":
                await message.answer(text="Добро пожаловать в меню Брокера E-CarsBurg.\n\n"
                                          "Воспользуйтесь кнопкой ниже для получения списка Ваших сделок.",
                                     reply_markup=kb_broker_main)
            elif department == "carrier":
                await message.answer(text="Добро пожаловать в меню Перевозчика автомобилей компании E-CarsBurg.\n\n"
                                          "Воспользуйтесь кнопкой ниже для получения списка Ваших сделок.",
                                     reply_markup=kb_carrier_main)
            else:
                await message.answer("Отдел не указан в вашем профиле")

        except SQLAlchemyError as e:
            logging.error(f"Database error in /start: {e}")
            await message.answer("Произошла ошибка при обработке запроса")
        except Exception as e:
            logging.error(f"Unexpected error in /start: {e}")
            await message.answer("Произошла непредвиденная ошибка")

