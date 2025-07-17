from aiogram import Router, F
from aiogram.types import CallbackQuery

callback_check_status_buyer_router = Router()

@callback_check_status_buyer_router.callback_query(F.data == "check_status_buyer")
async def callback_check_status_buyer(callback_query: CallbackQuery):
    pass
