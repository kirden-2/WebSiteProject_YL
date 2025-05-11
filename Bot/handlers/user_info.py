from http.client import responses

import requests
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from Bot.keyboards.inline_kbs import send_change_account_data_kb, send_start_login_kb
from config import SITE_API

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
        response = requests.post(f'{SITE_API}/user_info', json={'chat_id': chat_id}).json()

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
    await call.message.answer(
        'Введите старый пароль и новый пароль по формату: "старый_пароль;новый_пароль;повтор_пароля"')


@user_info_router.message(User_info_states.Change_password)
async def change_password(message: Message, state: FSMContext):
    parts = message.text.split(';')
    if len(parts) != 3:
        await message.answer('Неверный формат, повторите попытку "старый_пароль;новый_пароль;повтор_пароля"')
        return

    old_pas, new_pas, again_new_pas = parts
    try:
        response = requests.put(f'{SITE_API}/change_account_data/password',
                                json={'chat_id': message.chat.id,
                                      'old_password': old_pas,
                                      'new_password': new_pas,
                                      'again_new_password': again_new_pas}).json()
    except requests.RequestException:
        await message.answer('Не удалось связаться с сервером. Попробуйте позже.')
        return

    if response.get('success', ''):
        await message.answer('Пароль успешно изменен', reply_markup=send_start_login_kb())
        await state.set_state(User_info_states.Success_changes)
    else:
        error = response.get('error', 'Неизвестная ошибка')
        await message.answer(f'Ошибка: {error}')


@user_info_router.callback_query(F.data == 'change_email')
async def change_email(call: CallbackQuery, state: FSMContext):
    await state.set_state(User_info_states.Change_email)
    await call.message.answer('Введите новый email')


@user_info_router.message(User_info_states.Change_email)
async def continue_change_email(message: Message, state: FSMContext):
    try:
        response = requests.put(f'{SITE_API}/change_account_data/email',
                                json={'chat_id': message.chat.id,
                                      'new_email': message.text}).json()
    except requests.RequestException:
        await message.answer('Не удалось связаться с сервером. Попробуйте позже.')
        return

    if response.get('success', ''):
        await message.answer('Email успешно изменен', reply_markup=send_start_login_kb())
        await state.set_state(User_info_states.Success_changes)
    else:
        error = response.get('error', 'Неизвестная ошибка')
        await message.answer(f'Ошибка: {error}')


@user_info_router.callback_query(F.data == 'change_description')
async def change_description(call: CallbackQuery, state: FSMContext):
    await state.set_state(User_info_states.Change_description)
    await call.message.answer('Введите новое описание вашего профиля')


@user_info_router.message(User_info_states.Change_description)
async def continue_change_description(message: Message, state: FSMContext):
    try:
        response = requests.put(f'{SITE_API}/change_account_data/description',
                                json={'chat_id': message.chat.id,
                                      'new_description': message.text}).json()
    except requests.RequestException:
        await message.answer('Не удалось связаться с сервером. Попробуйте позже.')
        return

    if response.get('success', ''):
        await message.answer('Описание профиля успешно изменено', reply_markup=send_start_login_kb())
        await state.set_state(User_info_states.Success_changes)
    else:
        error = response.get('error', 'Неизвестная ошибка')
        await message.answer(f'Ошибка: {error}')
