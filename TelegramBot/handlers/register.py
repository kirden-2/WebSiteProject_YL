from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from TelegramBot.keyboards.inline_kbs import send_register_kb, send_cancel_kb, send_retry_reg_kb, send_start_login_kb, \
    send_start_not_login_kb
from config import SITE_API, BOT_TEXTS
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

    await call.message.edit_text(BOT_TEXTS["choose_reg_way"], reply_markup=send_register_kb())


@register_route.callback_query(F.data == 'telegram_reg')
async def tg_reg(call: CallbackQuery, state: FSMContext):
    if call.from_user.username:
        await call.message.edit_text(BOT_TEXTS["tg_info"], reply_markup=send_cancel_kb())
        await state.update_data(nick_name=call.from_user.username)
        await state.set_state(RegForm.password)
    else:
        await call.message.edit_text(BOT_TEXTS["tg_username_required"],
                                     reply_markup=send_retry_reg_kb())
    await call.answer()


@register_route.callback_query(F.data == 'default_reg')
async def set_nick_name(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(BOT_TEXTS["ask_nickname"], reply_markup=send_cancel_kb())
    await state.set_state(RegForm.nick_name)


@register_route.message(RegForm.nick_name)
async def set_password(message: Message, state: FSMContext):
    await state.update_data(nick_name=message.text)
    await message.answer(BOT_TEXTS["ask_password"], reply_markup=send_cancel_kb())
    await state.set_state(RegForm.password)


@register_route.message(RegForm.password)
async def set_password_again(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer(BOT_TEXTS["ask_repeat_password"], reply_markup=send_cancel_kb())
    await state.set_state(RegForm.password_again)


@register_route.message(RegForm.password_again)
async def check_register(message: Message, state: FSMContext):
    await state.update_data(password_again=message.text)
    await state.set_state(None)
    data = await state.get_data()
    payload = {'nick_name': data['nick_name'],
               'password': data['password'],
               'password_again': data['password_again'],
               'chat_id': message.chat.id}

    url = f'{SITE_API}/register'

    reg_resp = requests.post(url, json=payload).json()

    if reg_resp.get('success'):
        url = f'{SITE_API}/login'

        login_resp = requests.post(url, json=payload).json()

        if login_resp.get('success'):
            await message.answer(BOT_TEXTS["success_register"], reply_markup=send_start_login_kb())
        else:
            await message.answer(BOT_TEXTS["error_login_after_reg"],
                                 reply_markup=send_start_not_login_kb())
    else:
        await message.answer(reg_resp.get('user_message', BOT_TEXTS['other_error']), reply_markup=send_retry_reg_kb())
