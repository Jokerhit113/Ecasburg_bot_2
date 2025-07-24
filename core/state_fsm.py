from aiogram.fsm.state import StatesGroup, State


class NewUser(StatesGroup):
    waiting_for_departament = State()
    waiting_for_user_id = State()
    waiting_for_name = State()

class NewDeals(StatesGroup):
    waiting_for_id_deal = State()
    waiting_for_buyer_name = State()
    waiting_for_march_car = State()
    waiting_for_vin_code = State()
    waiting_for_photo_car = State()

class Admin(StatesGroup):
    waiting_for_transfer_photo_car = State()
    waiting_for_ready_for_issue_car = State()
    waiting_for_text_additional_options_yes_no = State()
    waiting_for_text_additional_options = State()
    waiting_for_load_contract = State()

class Buyer(StatesGroup):
    waiting_for_feedback_buyer = State()
    waiting_for_upload_inn = State()
    waiting_for_question_call = State()
    waiting_for_upload_payment_document_invoice_to_buyer = State()
    waiting_for_get_snils = State()
    waiting_for_get_registration_elpts = State()
    waiting_for_have_car = State()
    waiting_for_imported_yes_no = State()
    waiting_for_driver_license = State()
    waiting_for_email_address = State()
    waiting_for_actual_address_of_residence = State()
    waiting_for_get_cash_flow_statement = State()
    waiting_for_get_foreign_currency_account_statement = State()
    waiting_for_complete_load = State()
    waiting_for_payment = State()
    waiting_for_get_passport = State()
    waiting_phone_number_buyer = State()

class Provider(StatesGroup):
    waiting_for_car_go_to_rf = State()
    waiting_for_photo_buy_car = State()
    waiting_for_car_before_border = State()
    waiting_for_car_delivered_border = State()
    waiting_for_load_docs_car_provider = State()
    waiting_for_delivery_time_car_to_provider = State()
    waiting_for_delivery_time_car_to_border = State()

class Broker(StatesGroup):
    waiting_for_payment_invoice_to_buyer_text = State()
    waiting_for_payment_invoice_to_buyer = State()
    waiting_for_uin_text = State()
    waiting_for_cmr_file = State()
    waiting_for_reason_provider = State()
    waiting_for_reason_buyer = State()
    waiting_for_documents_broker = State()

class Carrier(StatesGroup):
    waiting_for_get_report_get_car = State()
    waiting_for_get_report_load_car = State()
    waiting_for_get_docs_car_carrier = State()