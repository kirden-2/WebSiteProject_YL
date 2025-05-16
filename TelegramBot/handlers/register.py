from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from TelegramBot.keyboards.inline_kbs import send_register_kb, send_cancel_kb, send_retry_reg_kb, send_start_login_kb, \
    send_start_not_login_kb
from TelegramBot.utils import fetch_post
from TelegramBot.config import BOT_TEXTS

register_route = Router()


class RegForm(StatesGroup):
    nick_name = State()
    password = State()
    password_again = State()


@register_route.callback_query(F.data == 'register')
async def register(call: CallbackQuery, state: FSMContext):
    await state.clear()

    await call.message.edit_text(BOT_TEXTS["choose_reg_way"],
                                 reply_markup=send_register_kb(),
                                 parse_mode="HTML")


@register_route.callback_query(F.data == 'telegram_reg')
async def tg_reg(call: CallbackQuery, state: FSMContext):
    if call.from_user.username:
        await call.message.edit_text(BOT_TEXTS["ask_password"],
                                     reply_markup=send_cancel_kb(),
                                     parse_mode="HTML")
        await state.update_data(nick_name=call.from_user.username)
        await state.set_state(RegForm.password)
    else:
        await call.message.edit_text(BOT_TEXTS["tg_username_required"],
                                     reply_markup=send_retry_reg_kb(),
                                     parse_mode="HTML")
    await call.answer()


@register_route.callback_query(F.data == 'default_reg')
async def default_reg(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(BOT_TEXTS["ask_nickname"],
                                 reply_markup=send_cancel_kb(),
                                 parse_mode="HTML")
    await state.set_state(RegForm.nick_name)


@register_route.message(RegForm.nick_name)
async def set_nickname(message: Message, state: FSMContext):
    await state.update_data(nick_name=message.text)
    await message.answer(BOT_TEXTS["ask_password"],
                         reply_markup=send_cancel_kb(),
                         parse_mode="HTML")
    await state.set_state(RegForm.password)


@register_route.message(RegForm.password)
async def set_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    await message.answer(BOT_TEXTS["ask_repeat_password"],
                         reply_markup=send_cancel_kb(),
                         parse_mode="HTML")
    await state.set_state(RegForm.password_again)


@register_route.message(RegForm.password_again)
async def set_password_again(message: Message, state: FSMContext):
    await state.update_data(password_again=message.text)
    await reg_finish(state, message)


async def reg_finish(state, message):
    data = await state.get_data()
    response, status = await fetch_post('/register',
                                        {'nick_name': data.get('nick_name'),
                                         'password': data.get('password'),
                                         'password_again': data.get('password_again'),
                                         'chat_id': message.chat.id}
                                        )

    if status == 200 and response.get('success'):
        response, status = await fetch_post('/login',
                                            {'nick_name': data.get('nick_name'),
                                             'password': data.get('password'),
                                             'chat_id': message.chat.id}
                                            )

        if status == 200 and response.get('success'):
            await message.answer(BOT_TEXTS["success_register"],
                                 reply_markup=send_start_login_kb(),
                                 parse_mode="HTML")
        else:
            await message.answer(BOT_TEXTS["error_login_after_reg"],
                                 reply_markup=send_start_not_login_kb(),
                                 parse_mode="HTML")

        await state.clear()
    else:
        await message.answer(response.get('user_message', BOT_TEXTS['generic_error']),
                             reply_markup=send_retry_reg_kb(),
                             parse_mode="HTML")
