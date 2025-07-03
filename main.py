import logging

from aiogram import Bot, Router, Dispatcher
import asyncio

from callback.callback_add_new_deal import add_new_deal_router
from callback.callback_add_user import callback_add_user_router
from callback.callback_delete_user import callback_delete_user_router
from callback.callback_other import callback_other_router
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


    await dp.start_polling(bot)




if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Работа бота завершена")
