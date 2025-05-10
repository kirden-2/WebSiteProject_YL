from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, LoginUrl, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from Bot.code.keyboards.inline_kbs import send_login_kb, send_cancel_kb, send_retry_login_kb, send_start_login_kb

from .check_login import check_user_login_now
from ..config import SITE_API

import requests

login_router = Router()


class LoginForm(StatesGroup):
    login_state = State()
    tg_login_state = State()


@login_router.callback_query(F.data == 'login')
async def login(call: CallbackQuery):
    await call.message.edit_text('Выберите подходящий для вас способ авторизации', reply_markup=send_login_kb())
    await call.answer()


@login_router.callback_query(F.data == 'default_log')
async def default_login(call: CallbackQuery, state: FSMContext):
    await state.set_state(LoginForm.login_state)
    await call.message.edit_text(
        'Введите через знак ";" по очереди:\nИмя пользователя;\n'
        'Пароль',
        reply_markup=send_cancel_kb())
    await call.answer()


@login_router.callback_query(F.data == 'telegram_log')
async def telegram_log(call: CallbackQuery, state: FSMContext):
    await state.set_state(LoginForm.tg_login_state)
    await call.message.edit_text(
        'Введите пароль от учетной записи',
        reply_markup=send_cancel_kb())
    await call.answer()


@login_router.message(LoginForm.login_state)
async def check_login(message: Message):
    if check_user_login_now(message.chat.id):
        await message.answer('Вы авторизованы на данный момент')
        return
    current_data = [value.strip() for value in message.text.split(';')]
    try:
        json = {'nick_name': current_data[0],
                'password': current_data[1],
                'chat_id': message.chat.id}
        req = requests.post(f"{SITE_API}/login", json=json).json()
        if req['success']:
            await message.answer('Авторизация прошла успешно', reply_markup=send_start_login_kb())
    except IndexError:
        await message.answer(f'Введенные данные не соответствуют формату. Повторите попытку',
                             reply_markup=send_retry_login_kb())
    except KeyError:
        await message.answer(f'{req["error"]}. Повторите попытку')
    except ConnectionError:
        await message.answer(
            f'Не удается установить подключение с нашим сайтом. Мы уже работаем над устранением проблемы.')


@login_router.message(LoginForm.tg_login_state)
async def check_tg_login(message: Message):
    if check_user_login_now(message.chat.id):
        await message.answer('Вы авторизованы на данный момент')
        return
    try:
        json = {'nick_name': f'{message.from_user.first_name}_{message.from_user.last_name}',
                'password': message.text,
                'chat_id': message.chat.id}
        req = requests.post(f"{SITE_API}/login", json=json).json()
        if req['success']:
            await message.answer('Авторизация прошла успешно', reply_markup=send_start_login_kb())
    except IndexError:
        await message.answer(f'Введенные данные не соответствуют формату. Повторите попытку',
                             reply_markup=send_retry_login_kb())
    except KeyError:
        await message.answer(f'{req["error"]}. Повторите попытку')
    except ConnectionError:
        await message.answer(
            f'Не удается установить подключение с нашим сайтом. Мы уже работаем над устранением проблемы.')
