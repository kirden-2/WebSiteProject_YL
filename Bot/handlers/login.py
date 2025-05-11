from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from Bot.keyboards.inline_kbs import send_login_kb, send_cancel_kb, send_retry_login_kb, send_start_login_kb

from .check_login import check_user_login_now
from config import SITE_API

import requests

login_router = Router()


class LoginForm(StatesGroup):
    login_state = State()
    tg_login_state = State()


@login_router.callback_query(F.data == 'login')
async def login(call: CallbackQuery):
    await call.message.edit_text(
        'Выберите способ авторизации',
        reply_markup=send_login_kb()
    )
    await call.answer()


@login_router.callback_query(F.data == 'default_log')
async def default_login(call: CallbackQuery, state: FSMContext):
    await state.set_state(LoginForm.login_state)
    await call.message.edit_text(
        'Введите: Имя;Пароль',
        reply_markup=send_cancel_kb()
    )
    await call.answer()


@login_router.message(LoginForm.login_state)
async def check_login(message: Message):
    if check_user_login_now(message.chat.id):
        return await message.answer('Вы уже авторизованы')

    parts = [v.strip() for v in message.text.split(';')]
    if len(parts) != 2:
        return await message.answer(
            'Неверный формат. Введите "Имя;Пароль"',
            reply_markup=send_retry_login_kb()
        )

    payload = {
        'nick_name': parts[0],
        'password': parts[1],
        'chat_id': message.chat.id
    }

    url = f"{SITE_API}/login"
    try:
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return await message.answer('Ошибка связи с сервером. Попробуйте позже.')
    except ValueError:
        return await message.answer('Некорректный ответ от сервера. Попробуйте позже.')

    if data.get('success', ''):
        await message.answer('Авторизация прошла успешно', reply_markup=send_start_login_kb())
    else:
        await message.answer(
            f"{data.get('error', 'Неизвестная ошибка')}. Повторите попытку",
            reply_markup=send_retry_login_kb()
        )
