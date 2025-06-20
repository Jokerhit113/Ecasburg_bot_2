from aiogram import Bot, Dispatcher
from aiogram.filters import Command
import asyncio

from aiogram.types import Message

from settings import TOKKEN_BOT

bot = Bot(token=TOKKEN_BOT)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.reply(f"Привет {message.from_user.first_name}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Работа бота завершена")
