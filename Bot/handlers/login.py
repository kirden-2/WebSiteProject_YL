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
    nick_name = State()
    password = State()


@login_router.callback_query(F.data == 'login')
async def login(call: CallbackQuery):
    await call.message.edit_text(
        'Выберите способ авторизации',
        reply_markup=send_login_kb())


@login_router.callback_query(F.data == 'default_log')
async def set_nick_name(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        'Введите имя пользователя',
        reply_markup=send_cancel_kb())
    await state.set_state(LoginForm.nick_name)


@login_router.message(LoginForm.nick_name)
async def set_password(message: Message, state: FSMContext):
    await state.update_data(nick_name=message.text)
    await message.answer('Введите пароль от учетной записи', reply_markup=send_cancel_kb())
    await state.set_state(LoginForm.password)


@login_router.message(LoginForm.password)
async def check_login(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    if check_user_login_now(message.chat.id):
        return await message.answer('Вы уже авторизованы', reply_markup=send_start_login_kb())

    login_data = await state.get_data()

    payload = {
        'nick_name': login_data['nick_name'],
        'password': login_data['password'],
        'chat_id': message.chat.id
    }

    url = f"{SITE_API}/login"
    try:
        resp = requests.post(url, json=payload, timeout=5)
        data = resp.json()
    except ValueError:
        return await message.answer(
            'Некорректный ответ от сервера. Попробуйте позже.'
        )

    if data.get('success'):
        await message.answer('Авторизация прошла успешно', reply_markup=send_start_login_kb())
    else:
        await message.answer(
            f"{data.get('error', 'Неизвестная ошибка')}. Повторите попытку",
            reply_markup=send_retry_login_kb()
        )
