from aiogram import Router, F
from aiogram.types import Message

get_video_id_router = Router()

@get_video_id_router.message(F.video)
async def video_get_video_id(message: Message):
    await message.answer(text=f"{message.video.file_id}")
