from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from Bot.code.keyboards.inline_kbs import send_start_kb

start_router = Router()

@start_router.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer('Приветствуем в нашем боте. Вы можете тут осмотреться или зарегистрироваться/войти, чтобы получить больше возможностей',
                         reply_markup=send_start_kb())