from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from TelegramBot.keyboards.inline_kbs import send_login_kb, send_cancel_kb, send_retry_login_kb, send_start_login_kb

from TelegramBot.check_login import check_user_login_now
from TelegramBot.config import BOT_TEXTS

from TelegramBot.utils import fetch_post

login_router = Router()


class LoginForm(StatesGroup):
    nick_name = State()
    password = State()


@login_router.callback_query(F.data == 'login')
async def login(call: CallbackQuery):
    await call.message.edit_text(BOT_TEXTS['choose_login_way'], reply_markup=send_login_kb(),
                                 parse_mode="HTML")


@login_router.callback_query(F.data == 'default_log')
async def default_log(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(BOT_TEXTS["ask_nickname"], reply_markup=send_cancel_kb(),
                                 parse_mode="HTML")
    await state.set_state(LoginForm.nick_name)


@login_router.callback_query(F.data == 'telegram_log')
async def tg_login(call: CallbackQuery, state: FSMContext):
    if call.from_user.username:
        await state.set_state(LoginForm.password)
        await state.update_data(nick_name=call.from_user.username)
    else:
        await call.message.edit_text(BOT_TEXTS["tg_username_required"],
                                     reply_markup=send_retry_login_kb(),
                                     parse_mode="HTML")


@login_router.message(LoginForm.nick_name)
async def set_nickname(message: Message, state: FSMContext):
    await state.update_data(nick_name=message.text)
    await message.answer(BOT_TEXTS["ask_password"], reply_markup=send_cancel_kb(),
                         parse_mode="HTML")
    await state.set_state(LoginForm.password)


@login_router.message(LoginForm.password)
async def set_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await log_finish(state, message)


async def log_finish(state, message):
    if await check_user_login_now(message.chat.id):
        return await message.answer(BOT_TEXTS["already_logged_in"], reply_markup=send_start_login_kb(),
                                    parse_mode="HTML")

    login_data = await state.get_data()

    response, status = await fetch_post('/login',
                                        {'nick_name': login_data['nick_name'],
                                         'password': login_data['password'],
                                         'chat_id': message.chat.id})

    if status == 200 and response.get('success'):
        await message.answer(BOT_TEXTS['success_login'], reply_markup=send_start_login_kb(),
                             parse_mode="HTML")
    else:
        await message.answer(response.get('user_message', BOT_TEXTS['generic_error']),
                             reply_markup=send_retry_login_kb(),
                             parse_mode="HTML")
