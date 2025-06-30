from aiogram import Router, Bot
from aiogram.types import Message, InputMediaPhoto
from aiogram.filters import Command
from sqlalchemy import Column, Integer, String, select, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, selectinload
import logging

logger = logging.getLogger(__name__)
router_test2 = Router()

# Асинхронный движок
engine = create_async_engine("sqlite+aiosqlite:///bot_test2.db")
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    photos = relationship("UserPhoto", back_populates="user", cascade="all, delete-orphan")


class UserPhoto(Base):
    __tablename__ = 'user_photos'
    id = Column(Integer, primary_key=True)
    file_id = Column(String(255), unique=True)  # Уникальный file_id
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="photos")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@router_test2.message(Command("start"))
async def cmd_start(message: Message):
    async with async_session() as session:
        try:
            user = await session.get(User, message.from_user.id)
            if not user:
                user = User(id=message.from_user.id, telegram_id=message.from_user.id)
                session.add(user)
                await session.commit()
                await message.answer("Вы зарегистрированы!")
            else:
                await message.answer("Вы уже зарегистрированы!")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in /start: {e}")
            await message.answer("Ошибка регистрации")


@router_test2.message(lambda m: m.photo)
async def save_photo(message: Message):
    async with async_session() as session:
        try:
            # Получаем пользователя с жадной загрузкой фото
            user = await session.get(
                User,
                message.from_user.id,
                options=[selectinload(User.photos)]
            )

            if not user:
                user = User(id=message.from_user.id, telegram_id=message.from_user.id)
                session.add(user)
                await session.flush()

            # Проверяем, есть ли уже такое фото
            file_id = message.photo[-1].file_id
            existing = await session.execute(
                select(UserPhoto)
                .where(UserPhoto.file_id == file_id)
            )
            if existing.scalar_one_or_none():
                await message.answer("Это фото уже сохранено!")
                return

            # Добавляем новое фото
            photo = UserPhoto(file_id=file_id, user_id=user.id)
            session.add(photo)
            await session.commit()

            # Получаем актуальное количество фото
            count = await session.scalar(
                select(UserPhoto)
                .where(UserPhoto.user_id == user.id)
            )
            await message.answer(f"Фото сохранено! Всего фото: {count}")

        except Exception as e:
            await session.rollback()
            logger.error(f"Error saving photo: {e}")
            await message.answer("Ошибка сохранения фото")


@router_test2.message(Command("myphotos"))
async def show_photos(message: Message, bot: Bot):
    async with async_session() as session:
        try:
            # Получаем пользователя с его фото
            user = await session.get(
                User,
                message.from_user.id,
                options=[selectinload(User.photos)]
            )

            if not user or not user.photos:
                await message.answer("Нет сохраненных фото")
                return

            # Группируем фото по 10
            for i in range(0, len(user.photos), 10):
                media_group = [
                    InputMediaPhoto(media=photo.file_id)
                    for photo in user.photos[i:i + 10]
                ]
                await bot.send_media_group(
                    chat_id=message.chat.id,
                    media=media_group
                )

        except Exception as e:
            logger.error(f"Error showing photos: {e}")
            await message.answer("Ошибка при получении фото")