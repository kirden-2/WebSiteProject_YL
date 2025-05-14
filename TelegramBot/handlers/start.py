import requests
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from TelegramBot.keyboards.inline_kbs import send_start_not_login_kb, send_start_login_kb
from .login import login_router
from .register import register_route
from .view_arts import view_arts_router
from .user_info import user_info_router

from .check_login import check_user_login_now

from config import SITE_API

start_router = Router()


class Start_states(StatesGroup):
    logout_state = State()


@login_router.message(Command('back'))
@register_route.message(Command('back'))
@view_arts_router.message(Command('back'))
@user_info_router.message(Command('back'))
@start_router.message(Command('start'))
@start_router.message(Start_states.logout_state)
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if check_user_login_now(message.chat.id):
        reply_markup = send_start_login_kb()
    else:
        reply_markup = send_start_not_login_kb()

    await message.answer(
        '''Приветствуем в нашем боте. Вы можете тут осмотреться или зарегистрироваться/войти, 
чтобы получить больше возможностей.\n
Используйте команду /back, чтобы вернуться в начало''',
        reply_markup=reply_markup)


@register_route.callback_query(F.data == 'back_to_start')
@login_router.callback_query(F.data == 'back_to_start')
@view_arts_router.callback_query(F.data == 'back_to_start')
@user_info_router.callback_query(F.data == 'back_to_start')
async def cmd_start(call: CallbackQuery, state: FSMContext):
    if check_user_login_now(call.message.chat.id):
        reply_markup = send_start_login_kb()
    else:
        reply_markup = send_start_not_login_kb()

    await call.message.edit_text(
        '''Приветствуем в нашем боте. Вы можете тут осмотреться или зарегистрироваться/войти, 
чтобы получить больше возможностей.\n
Используйте команду /back, чтобы вернуться в начало при необходимости''',
        reply_markup=reply_markup)


@start_router.callback_query(F.data == 'logout')
async def logout(call: CallbackQuery, state: FSMContext):
    await state.set_state(Start_states.logout_state)
    try:
        response = requests.post(f'{SITE_API}/logout', json={'chat_id': call.message.chat.id}).json()

        if response['success']:
            await call.message.edit_text('Вы успешно вышли из аккаунта', reply_markup=send_start_not_login_kb())
    except Exception:
        await call.message.edit_text('Не удалось выйти из учетной записи. Приносим извинения',
                                     reply_markup=send_start_login_kb())
