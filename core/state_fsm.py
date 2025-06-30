from aiogram.fsm.state import StatesGroup, State


class NewUser(StatesGroup):
    waiting_for_departament = State()
    waiting_for_user_id = State()
    waiting_for_name = State()