from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from Bot.code.keyboards.inline_kbs import send_start_not_login_kb
from .login import login_router
from .register import register_route
from .view_arts import view_arts_router

start_router = Router()


@login_router.message(Command('back'))
@register_route.message(Command('back'))
@view_arts_router.message(Command('back'))
@start_router.message(Command('start'))
async def cmd_start(message: Message):
    await message.answer(
        '''Приветствуем в нашем боте. Вы можете тут осмотреться или зарегистрироваться/войти, 
чтобы получить больше возможностей.\n
Используйте команду /back, чтобы вернуться в начало''',
        reply_markup=send_start_not_login_kb())


@register_route.callback_query(F.data == 'back_to_start')
@login_router.callback_query(F.data == 'back_to_start')
@view_arts_router.callback_query(F.data == 'back_to_start')
async def cmd_start(call: CallbackQuery):
    await call.message.answer(
        '''Приветствуем в нашем боте. Вы можете тут осмотреться или зарегистрироваться/войти, 
чтобы получить больше возможностей.\n
Используйте команду /back, чтобы вернуться в начало при необходимости''',
        reply_markup=send_start_not_login_kb())