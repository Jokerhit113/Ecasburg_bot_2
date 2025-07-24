import logging
from pathlib import Path

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy import select

from data_base.db_deals import deals_session, Deals
from settings import CHAT_LOG

callback_add_documents_buyer_router = Router()


@callback_add_documents_buyer_router.callback_query(F.data == "info_add_documents_buyer")
async def info_add_documents_buyer_info(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал: Информция о загрузке документов ")
    file = Path(f"setting/info_load_documents.txt")
    text = file.read_text(encoding='utf-8')
    builder = InlineKeyboardBuilder()
    builder.button(text=f"УДАЛИТЬ СООБЩЕНИЕ", callback_data=f"delete_message")
    builder.adjust(1)
    await callback.message.answer(text=text, reply_markup=builder.as_markup())
    media_group = MediaGroupBuilder()
    media_group.add_video(media="BAACAgIAAxkBAAI11miB_5G6flWMBeUubz10WFbJDaw4AAJTewACA6wJSNGTFKoeE8JLNgQ", caption="Инструкция: Как открыть счёт в Юанях в ВТБ приложении")
    media_group.add_video(media="BAACAgIAAxkBAAI12GiB_7sYohZMbFET-1eS0IBsAQd2AAJUewACA6wJSNQuclG8a00QNgQ", caption="Конвертируем Рубли в Юани")
    media_group.add_video(media="BAACAgIAAxkBAAI12miB__Cwp3B2ER5dZ62nNRzMjNzGAAIVfQACA6wJSBIEfEh_52hVNgQ", caption="Как оплачивать автомобиль")
    media_group.add_video(media="BAACAgIAAxkBAAI1x2iB_ffuFenoqFbMZ7d_adCG5-PlAAI3bQACA6wRSCr2HqlHN_YPNgQ", caption="Инструкция: Как получить Справку и Выписку с валютного счёта")
    await callback.message.answer_media_group(media=media_group.build())
    await callback.answer()

@callback_add_documents_buyer_router.callback_query(F.data == "kb_menu_load_docs")
async def kb_menu_load_docs(callback: CallbackQuery, state: FSMContext):
    caption = callback.message.caption
    deal_id = int(caption.split('\n')[0].split('Ваша Сделка №: ')[1])
    async with deals_session() as session:
        deal = await session.execute(
            select(Deals).where(Deals.deal_id == deal_id)
        )
        deal = deal.scalar_one_or_none()

        if not deal.payment_photo_id and not deal.payment_document_id:
            payment_confirmation_buyer_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            payment_confirmation_buyer_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.passport_photos and not deal.passport_documents:
            add_passport_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            add_passport_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.inn_photo and not deal.inn_docs:
            upload_inn_buyer_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            upload_inn_buyer_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.buyer_driver_license_photo and not deal.buyer_driver_license_docs:
            driver_license_load_buyer_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            driver_license_load_buyer_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.snils_buyer_photos and not deal.snils_buyer_docs:
            add_snils_buyer_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            add_snils_buyer_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.foreign_currency_account_statement_photo and not deal.foreign_currency_account_statement_docs:
            foreign_currency_account_statement_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            foreign_currency_account_statement_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.cash_flow_statement_photos and not deal.cash_flow_statement_docs:
            cash_flow_statement_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            cash_flow_statement_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.buyer_phone_number:
            fill_out_the_questionnaire_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            fill_out_the_questionnaire_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.elpts_registration_photo:
            get_elpts_registration_btn = "⚠️"  # Нет ни фото, ни видео
        else:
            get_elpts_registration_btn = "✅"  # Есть хотя бы что-то из этого

        if not deal.confirmation_of_acceptance_of_documents_from_buyer:
            confirmation_of_acceptance_of_documents_from_buyer = "⚠️"  # Нет ни фото, ни видео
        else:
            confirmation_of_acceptance_of_documents_from_buyer = "✅"  # Есть хотя бы что-то из этого

        await state.update_data(payment_confirmation_buyer_btn=payment_confirmation_buyer_btn,
                                add_passport_btn=add_passport_btn,
                                driver_license_load_buyer_btn=driver_license_load_buyer_btn,
                                add_snils_buyer_btn=add_snils_buyer_btn,
                                foreign_currency_account_statement_btn=foreign_currency_account_statement_btn,
                                cash_flow_statement_btn=cash_flow_statement_btn,
                                fill_out_the_questionnaire_btn=fill_out_the_questionnaire_btn,
                                get_elpts_registration_btn=get_elpts_registration_btn)


    builder = InlineKeyboardBuilder()
    builder.button(text=f"{payment_confirmation_buyer_btn} Подтвердить Оплату", callback_data="payment_confirmation_buyer")
    builder.button(text=f"{add_passport_btn} Паспорт", callback_data="add_passport")
    builder.button(text=f"{upload_inn_buyer_btn}ИНН", callback_data="upload_inn_buyer")
    builder.button(text=f"{driver_license_load_buyer_btn} Водительское Удостоверение", callback_data="driver_license_load_buyer")
    builder.button(text=f"{add_snils_buyer_btn} СНИЛС", callback_data="add_snils_buyer")
    builder.button(text=f"{foreign_currency_account_statement_btn} Выписка по валютному счету", callback_data="foreign_currency_account_statement")
    builder.button(text=f"{cash_flow_statement_btn} Справка о движении денежных средств по ВС", callback_data="cash_flow_statement")
    builder.button(text=f"{fill_out_the_questionnaire_btn} Заполнить Анкету", callback_data="fill_out_the_questionnaire")
    builder.button(text=f"{get_elpts_registration_btn} Загрузить Скрин с сайта ЭПТС", callback_data="get_elpts_registration")
    builder.button(text=f"{confirmation_of_acceptance_of_documents_from_buyer} Запросить проверку документов 🔍", callback_data="request_check_docs_from_the_broker")
    builder.button(text="⬅️ Назад", callback_data=f"deal_list_buyer_{deal_id}")
    builder.adjust(1)
    await callback.answer(text="Для Загрузки документов, выберите нужный пункт меню, и строго следуйте инструкциям.",
                          show_alert=True)
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n"
                f"Для Загрузки документов, выберите нужный пункт меню, и строго следуйте инструкциям.",
        reply_markup=builder.as_markup()
    )

@callback_add_documents_buyer_router.callback_query(F.data == "delete_message")
async def delete_message(callback: CallbackQuery, bot: Bot):
    await bot.send_message(chat_id=CHAT_LOG,
                           text=f"{callback.from_user.first_name} {callback.from_user.last_name} Покупатель выбрал: Удалить сообщение")
    await callback.message.delete()
