import logging
from typing import List, Union
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals
from data_base.db_users import user_session, User
from keyboard.inline_keyboard import kb_broker_main
from settings import CHAT_LOG

callback_end_deal_broker_router = Router()

async def send_media_chunks(
        bot: Bot,
        chat_id: int,
        media_items: Union[List[str], str, None],
        caption: str,
        media_type: str = "photo"
) -> None:
    """Отправляет медиафайлы частями по 10 штук с обработкой ошибок"""
    if not media_items:
        return

    # Нормализуем входные данные в список
    if isinstance(media_items, str):
        media_items = [media_items]
    elif not isinstance(media_items, list):
        logging.error(f"Invalid media_items type: {type(media_items)}")
        return

    # Фильтруем невалидные file_id
    valid_media = [m for m in media_items if m and isinstance(m, str) and len(m) > 20]

    if not valid_media:
        logging.warning("No valid media items found")
        return

    # Разбиваем на группы по 10 элементов
    chunk_size = 10
    for i in range(0, len(valid_media), chunk_size):
        chunk = valid_media[i:i + chunk_size]
        try:
            media_group = MediaGroupBuilder(caption=caption if i == 0 else "")

            for media_id in chunk:
                if media_type == "photo":
                    media_group.add_photo(media=media_id)
                elif media_type == "document":
                    media_group.add_document(media=media_id)

            await bot.send_media_group(chat_id=chat_id, media=media_group.build())
        except Exception as e:
            logging.error(f"Error sending media chunk {i}-{i + chunk_size}: {e}")


@callback_end_deal_broker_router.callback_query(F.data == "end_deal_broker")
async def end_deal_broker(callback: CallbackQuery, bot: Bot):

    text = callback.message.caption
    deal_id = text.split('\n')[0].split('Сделка №: ')[1]
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()
        if not deal:
            await callback.answer("Сделка не найдена")
            return
        await bot.send_message(chat_id=CHAT_LOG,
                               text=f"{callback.from_user.first_name} {callback.from_user.last_name} Брокер Выбрал Завершить сделку {deal_id}")

        async with user_session() as u_session:
            users = await u_session.execute(
                select(User).where(User.departament == "admin")
            )
            users = users.scalars().all()
            if users:
                message_text = (
                    f"Сделка №: {deal.deal_id}\n"
                    f"Покупатель: {deal.buy_user}\n"
                    f"Автомобиль: {deal.march_model}\n"
                    f"VIN: {deal.vin_code}\n"
                    f"Номер телефона: {deal.buyer_phone_number}"
                )
                # Проверка наличия документов
                if not deal.photo_docs_broker_id and not deal.document_doc_broker_id:
                    await callback.answer("Вы ещё не загрузили таможенные документы", show_alert=True)
                    return


                for user in users:
                    await bot.send_photo(
                        chat_id=user.user_id,
                        photo=deal.car_photo_id,
                        caption=f"️✅ БРОКЕР ЗАВЕРШИЛ РАБОТУ ПО СДЕЛКЕ\n\n"
                                f"{message_text}\n\n"
                                f"Таможенные Документы по автомобилю прилагаются ниже "
                    )
                    # Отправка фото документов с разбивкой на группы
                    if deal.photo_docs_broker_id:
                        await send_media_chunks(
                            bot=callback.bot,
                            chat_id=user.user_id,
                            media_items=deal.photo_docs_broker_id,
                            caption="Фото документов:",
                            media_type="photo"
                        )

                    # Отправка сканов документов с разбивкой на группы
                    if deal.document_doc_broker_id:
                        await send_media_chunks(
                            bot=callback.bot,
                            chat_id=user.user_id,
                            media_items=deal.document_doc_broker_id,
                            caption="Сканы документов:",
                            media_type="document"
                        )
            deal.broker_id = ""
            await session.commit()
        await callback.message.delete()
        await callback.answer("Благодарим Вас за проведённую работу, до встречи на следующих сделках!", show_alert=True)
        await callback.message.answer("Благодарим Вас за проведённую работу, до встречи на следующих сделках!")
        await callback.message.answer(text="Добро пожаловать в меню Брокера E-CarsBurg.\n\n"
                                  "Воспользуйтесь кнопкой ниже для получения списка Ваших сделок.",
                             reply_markup=kb_broker_main)