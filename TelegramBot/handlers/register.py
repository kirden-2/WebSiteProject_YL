from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from TelegramBot.keyboards.inline_kbs import send_register_kb, send_cancel_kb, send_retry_reg_kb, send_start_login_kb, \
    send_start_not_login_kb
from config import SITE_API
from .check_login import check_user_login_now

import requests

register_route = Router()


class RegForm(StatesGroup):
    nick_name = State()
    password = State()
    password_again = State()


@register_route.callback_query(F.data == 'register')
async def register(call: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()  # получаем текущий статус
    if current_state is not None:  # если статус не установлен, то ничего не делаем
        await state.clear()

    await call.message.edit_text('Выберите подходящий для вас способ регистрации.', reply_markup=send_register_kb())


@register_route.callback_query(F.data == 'telegram_reg')
async def tg_reg(call: CallbackQuery, state: FSMContext):
    if call.from_user.username:
        await call.message.edit_text('В качестве имени пользователя будет использовано ваше username.\n\n'
                                     'Введите желаемый пароль', reply_markup=send_cancel_kb())
        await state.update_data(nick_name=call.from_user.username)
        await state.set_state(RegForm.password)
    else:
        await call.message.edit_text("Для регистрации через Telegram необходимо указать username в настройках.",
                                     reply_markup=send_retry_reg_kb())
    await call.answer()


@register_route.callback_query(F.data == 'default_reg')
async def set_nick_name(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text('Введите желаемое имя пользователя', reply_markup=send_cancel_kb())
    await state.set_state(RegForm.nick_name)


@register_route.message(RegForm.nick_name)
async def set_password(message: Message, state: FSMContext):
    await state.update_data(nick_name=message.text)
    await message.answer('Введите пароль', reply_markup=send_cancel_kb())
    await state.set_state(RegForm.password)


@register_route.message(RegForm.password)
async def set_password_again(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer('Повторите введенный пароль', reply_markup=send_cancel_kb())
    await state.set_state(RegForm.password_again)


@register_route.message(RegForm.password_again)
async def check_register(message: Message, state: FSMContext):
    await state.update_data(password_again=message.text)
    await state.set_state(None)
    data = await state.get_data()
    payload = {'nick_name': data['nick_name'],
               'password': data['password'],
               'password_again': data['password_again']}

    try:
        resp = requests.post(f'{SITE_API}/register', json=payload, timeout=5)
        resp.raise_for_status()
        resp_data = resp.json()
    except ValueError:
        return await message.answer('Некорректный ответ от сервера. Попробуйте позже.')

    if resp_data.get('success'):
        try:
            check_user_login_now(message.chat.id)
            login_payload = {'nick_name': data['nick_name'],
                             'password': data['password'],
                             'chat_id': message.chat.id}
            login_resp = requests.post(f'{SITE_API}/login', json=login_payload)
            login_resp.raise_for_status()
            login_resp_data = login_resp.json()
        except requests.exceptions.HTTPError:
            await message.answer(
                'Не удалось автоматически войти в учетную запись, просим авторизоваться самостоятельно',
                reply_markup=send_start_not_login_kb())
        if login_resp_data.get('success'):
            await message.answer(
                'Регистрация прошла успешно, для заполнения остальных данных перейдите в раздел "Информация об учетной записи"',
                reply_markup=send_start_login_kb())
    else:
        await message.answer(
            f"{resp_data.get('error', 'Неизвестная ошибка')}.",
            reply_markup=send_retry_reg_kb())
