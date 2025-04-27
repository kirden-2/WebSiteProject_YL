from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from Bot.code.keyboards.inline_kbs import send_login_kb, send_cancel_kb, send_retry_login_kb, send_start_login_kb

import requests

login_router = Router()

api_site = 'http://127.0.0.1:5000/bot_api/login'


class LoginForm(StatesGroup):
    login_state = State()


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


@login_router.message(LoginForm.login_state)
async def check_login(message: Message):
    current_data = [value.strip() for value in message.text.split(';')]
    print(current_data)
    json = {'nick_name': current_data[0],
            'password': current_data[1]}
    try:
        req = requests.post(api_site, json=json).json()
        print(req)
        if req['success']:
            await message.answer('Авторизация прошла успешно прошла успешно', reply_markup=send_start_login_kb())
    except KeyError:
        await message.answer(f'{req["error"]}. Повторите попытку', reply_markup=send_retry_login_kb())
    except ConnectionError:
        await message.answer(
            f'Не удается установить подключение с нашим сайтом. Мы уже работаем над устранением проблемы.')
    except Exception:
        pass

