from aiogram import Bot, Router, Dispatcher
import asyncio

from callback.callback_admin_menu import callback_admin_router
from command import router_command
from data_base.db_users import init_users_db
from settings import TOKKEN_BOT

router = Router()


async def main():
    await init_users_db()  # Инициализация БД

    bot = Bot(token=TOKKEN_BOT)
    dp = Dispatcher()
    dp.include_router(router_command)
    dp.include_router(callback_admin_router)


    await dp.start_polling(bot)




if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Работа бота завершена")
