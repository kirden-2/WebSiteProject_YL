import requests
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from Bot.code.keyboards.inline_kbs import send_change_account_data_kb, send_start_login_kb
from .login import login_router
from .register import register_route
from .view_arts import view_arts_router

from .check_login import check_user_login_now

user_info_router = Router()


class User_info_states(StatesGroup):
    Change_password = State()
    Change_email = State()
    Change_description = State()
    Success_changes = State()


@user_info_router.callback_query(F.data == 'user_info')
@user_info_router.message(User_info_states.Success_changes)
async def get_user_info(call: CallbackQuery, state: FSMContext):
    await state.clear()

    chat_id = call.message.chat.id

    try:
        response = requests.get('http://127.0.0.1:5000/bot_api/get_user_info', json={'chat_id': chat_id}).json()

        await call.message.answer(f'Информация о пользователе:\n'
                                  f'\n'
                                  f'🙎‍♂️Имя пользователя: {response["user"]["nick_name"]}\n'
                                  f'🏷️id пользователя: {response["user"]["id"]}\n'
                                  f'📧email: {response["user"]["email"] if response["user"]["email"] else "не указан"}\n'
                                  f'✏️Описание профиля: \
{response["user"]["description"] if response["user"]["description"] else "не указано"}\n'
                                  f'💰Баланс: {response["user"]["balance"]}\n'
                                  f'🗓️Дата создания аккаунта: {response["user"]["creation_time"]}',
                                  reply_markup=send_change_account_data_kb())
    except Exception:
        await call.message.answer('Не удалось получить информацию о пользователе. Приносим извинения')


@user_info_router.callback_query(F.data == 'change_password')
async def password_confirm(call: CallbackQuery, state: FSMContext):
    await state.set_state(User_info_states.Change_password)
    await call.message.answer('Введите старый пароль и новый пароль по формату: "старый_пароль;новый_пароль"')


@user_info_router.message(User_info_states.Change_password)
async def change_password(message: Message, state: FSMContext):
    try:
        response = requests.put('http://127.0.0.1:5000/bot_api/change_data/password',
                                json={'chat_id': message.chat.id, 'old_password': message.text.split(';')[0],
                                      'new_password': message.text.split(';')[1]}).json()
        if response['success']:
            await message.answer('Пароль успешно изменен', send_start_login_kb())
            await state.set_state(User_info_states.Success_changes)
    except KeyError:
        await message.answer(f'{response["error"]}. Повторите попытку')

    except Exception:
        await message.answer('Произошла ошибка. Приносим извинения')


@user_info_router.callback_query(F.data == 'change_email')
async def change_email(call: CallbackQuery, state: FSMContext):
    await state.set_state(User_info_states.Change_email)
    await call.message.answer('Введите новый email')


@user_info_router.message(User_info_states.Change_email)
async def continue_change_email(message: Message, state: FSMContext):
    try:
        response = requests.put('http://127.0.0.1:5000/bot_api/change_data/email',
                                json={'chat_id': message.chat.id, 'new_email': message.text}).json()

        if response['success']:
            await message.answer('Email успешно изменен', reply_markup=send_start_login_kb())
            await state.set_state(User_info_states.Success_changes)

    except KeyError:
        await message.answer(f'{response["error"]}. Повторите попытку')
    except Exception:
        await message.answer('Произошла ошибка. Приносим извинения')


@user_info_router.callback_query(F.data == 'change_description')
async def change_description(call: CallbackQuery, state: FSMContext):
    await state.set_state(User_info_states.Change_description)
    await call.message.answer('Введите новое описание вашего профиля')


@user_info_router.message(User_info_states.Change_description)
async def continue_change_description(message: Message, state: FSMContext):
    try:
        response = requests.put('http://127.0.0.1:5000/bot_api/change_data/description',
                                json={'chat_id': message.chat.id, 'new_description': message.text}).json()

        if response['success']:
            await message.answer('Описание профиля успешно изменено', reply_markup=send_start_login_kb())
            await state.set_state(User_info_states.Success_changes)

    except KeyError:
        await message.answer(f'{response["error"]}. Повторите попытку')
    except Exception:
        await message.answer('Произошла ошибка. Приносим извинения')
