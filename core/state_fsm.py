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

class Buyer(StatesGroup):
    waiting_for_complete_load = State
    waiting_for_payment = State()
    waiting_for_get_passport = State()