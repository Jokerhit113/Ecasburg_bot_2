import logging
from aiogram import Bot, Router, Dispatcher
import asyncio

from callback_admins.callback_add_additional_options import callback_add_additional_options_router
from callback_admins.callback_add_contract import callback_add_contract_router
from callback_admins.callback_add_new_deal import add_new_deal_router
from callback_admins.callback_add_user import callback_add_user_router
from callback_admins.callback_change_broker import callback_change_broker_router
from callback_admins.callback_change_buyer import callback_change_buyer_router
from callback_admins.callback_change_carrier import callback_change_carrier_router
from callback_admins.callback_change_provider import callback_change_provider_router
from callback_admins.callback_delete_user import callback_delete_user_router
from callback_admins.callback_car_is_ready_for_delivery import callback_car_is_ready_for_delivery_router
from callback_admins.callback_get_all_data_deal import callback_get_all_data_deal_router
from callback_admins.callback_get_deals_list import callback_get_deals_list_router
from callback_admins.callback_other import callback_other_router
from callback_admins.callback_status_deal import callback_status_deal_router
from callback_admins.callback_transaction_actions import callback_transaction_actions_router
from callback_broker.callback_check_deals_broker import callback_check_deals_broker_router
from callback_broker.callback_check_the_buyer_documents import callback_check_the_buyer_documents_router
from callback_broker.callback_check_the_documents_for_the_car import callback_check_the_documents_for_the_car_router
from callback_broker.callback_end_deal_broker import callback_end_deal_broker_router
from callback_broker.callback_load_docs_broker import callback_load_docs_broker_router
from callback_broker.callback_upload_a_payment_invoice_to_buyer import callback_upload_a_payment_invoice_to_buyer_router
from callback_buyer.callback_add_buyer_driver_license import callback_add_buyer_driver_license_router
from callback_buyer.callback_add_documents_buyer import callback_add_documents_buyer_router
from callback_buyer.callback_add_inn_buyer import callback_add_inn_buyer_router
from callback_buyer.callback_add_passport import callback_add_passport_router
from callback_buyer.callback_call_manager import callback_call_manager_router
from callback_buyer.callback_cash_flow_statement import callback_cash_flow_statement_router
from callback_buyer.callback_check_deals_buyer import callback_check_deals_buyer_router
from callback_buyer.callback_check_status_buyer import callback_check_status_buyer_router
from callback_buyer.callback_fill_out_the_questionnaire import callback_fill_out_the_questionnaire_router
from callback_buyer.callback_foreign_currency_account_statement import \
    callback_foreign_currency_account_statement_router
from callback_buyer.callback_get_elpts_registration import callback_get_elpts_registration_router
from callback_buyer.callback_get_snils_buyer import callback_get_snils_buyer_router
from callback_buyer.callback_payment_confirmation import callback_payment_confirmation_buyer_router
from callback_buyer.callback_request_check_docs_from_the_broker import \
    callback_request_check_docs_from_the_broker_router
from callback_carrier.callback_check_deals_carrier import callback_check_deals_carrier_router
from callback_carrier.callback_load_docs_carrier import callback_load_docs_carrier_router
from callback_carrier.callback_report_of_loading_a_vehicle_for_transportation import \
    callback_report_of_loading_a_vehicle_for_transportation_router
from callback_carrier.callback_report_of_receiving_a_car_at_the_border import \
    callback_report_of_receiving_a_car_at_the_border_router
from callback_provider.callback_buy_car_provider import callback_buy_car_provider_router
from callback_provider.callback_car_before_border import callback_car_before_border_router
from callback_provider.callback_car_delivered_border import callback_car_delivered_border_router
from callback_provider.callback_car_go_to_rf import callback_car_go_to_rf_router
from callback_provider.callback_check_deals_provider import callback_check_deals_provider_router
from callback_provider.callback_confirmation_payment_buyer_provider import \
    callback_confirmation_payment_buyer_provider_router
from callback_provider.callback_load_docs_car_provider import callback_load_docs_car_provider_router
from command import router_command
from data_base.db_deals import init_deals_db
from data_base.db_users import init_users_db
from settings import TOKKEN_BOT

router = Router()
logging.basicConfig(level=logging.INFO)

async def main():
    await init_users_db()
    await init_deals_db()

    bot = Bot(token=TOKKEN_BOT)
    dp = Dispatcher()
    dp.include_router(router_command)
    dp.include_router(callback_add_user_router)
    dp.include_router(callback_delete_user_router)
    dp.include_router(callback_other_router)
    dp.include_router(add_new_deal_router)
    dp.include_router(callback_get_deals_list_router)
    dp.include_router(callback_change_provider_router)
    dp.include_router(callback_change_broker_router)
    dp.include_router(callback_change_carrier_router)
    dp.include_router(callback_change_buyer_router)
    dp.include_router(callback_status_deal_router)
    dp.include_router(callback_payment_confirmation_buyer_router)
    dp.include_router(callback_confirmation_payment_buyer_provider_router)
    dp.include_router(callback_add_documents_buyer_router)
    dp.include_router(callback_add_passport_router)
    dp.include_router(callback_foreign_currency_account_statement_router)
    dp.include_router(callback_cash_flow_statement_router)
    dp.include_router(callback_fill_out_the_questionnaire_router)
    dp.include_router(callback_get_elpts_registration_router)
    dp.include_router(callback_check_deals_provider_router)
    dp.include_router(callback_buy_car_provider_router)
    dp.include_router(callback_car_before_border_router)
    dp.include_router(callback_car_delivered_border_router)
    dp.include_router(callback_load_docs_car_provider_router)
    dp.include_router(callback_check_deals_buyer_router)
    dp.include_router(callback_get_snils_buyer_router)
    dp.include_router(callback_check_deals_broker_router)
    dp.include_router(callback_check_the_documents_for_the_car_router)
    dp.include_router(callback_check_the_buyer_documents_router)
    dp.include_router(callback_load_docs_broker_router)
    dp.include_router(callback_add_contract_router)
    dp.include_router(callback_check_deals_carrier_router)
    dp.include_router(callback_report_of_receiving_a_car_at_the_border_router)
    dp.include_router(callback_report_of_loading_a_vehicle_for_transportation_router)
    dp.include_router(callback_load_docs_carrier_router)
    dp.include_router(callback_add_buyer_driver_license_router)
    dp.include_router(callback_upload_a_payment_invoice_to_buyer_router)
    dp.include_router(callback_request_check_docs_from_the_broker_router)
    dp.include_router(callback_call_manager_router)
    dp.include_router(callback_check_status_buyer_router)
    dp.include_router(callback_transaction_actions_router)
    dp.include_router(callback_add_additional_options_router)
    dp.include_router(callback_end_deal_broker_router)
    dp.include_router(callback_add_inn_buyer_router)
    dp.include_router(callback_car_go_to_rf_router)
    dp.include_router(callback_get_all_data_deal_router)
    dp.include_router(callback_car_is_ready_for_delivery_router)

    await dp.start_polling(bot)




if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Работа бота завершена")
