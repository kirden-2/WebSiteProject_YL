from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from TelegramBot.keyboards.inline_kbs import send_change_account_data_kb, send_start_login_kb, \
    send_cancellation_to_user_info, \
    send_profile_to_user_info
from TelegramBot.utils import fetch_post
from TelegramBot.config import BOT_TEXTS

user_info_router = Router()


class UserInfoStates(StatesGroup):
    change_password = State()
    change_email = State()
    change_description = State()


class UpdatePassword(StatesGroup):
    old_pas = State()
    new_pas = State()
    again_new_pas = State()


async def update_password(data, chat_id):
    payload = {
        'chat_id': chat_id,
        'old_password': data.get('old_pas', ''),
        'new_password': data.get('new_pas', ''),
        'again_new_password': data.get('again_new_pas', '')
    }
    response, status = await fetch_post('/change_account_data/password', payload)
    return response


@user_info_router.callback_query(F.data == 'user_info')
async def get_user_info(call: CallbackQuery, state: FSMContext):
    await state.clear()
    chat_id = call.message.chat.id
    response, status = await fetch_post('/user_info', {'chat_id': chat_id})
    if status != 200 or not response.get('success'):
        await call.message.edit_text(
            BOT_TEXTS['network_error'],
            reply_markup=send_start_login_kb(),
            parse_mode='HTML')
        return

    user = response['user']
    text = BOT_TEXTS['profile_intro'].format(
        nick_name=user['nick_name'], id=user['id'], email=user['email'] or 'не указан',
        description=user['description'] or 'не указано', balance=user['balance'], creation_time=user['creation_time']
    )
    await call.message.edit_text(
        text,
        reply_markup=send_change_account_data_kb(),
        parse_mode='HTML')


@user_info_router.callback_query(F.data == 'change_password')
async def password_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer(BOT_TEXTS['ask_current_password'],
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=send_cancellation_to_user_info()
                              ),
                              parse_mode='HTML')
    await state.set_state(UpdatePassword.old_pas)


@user_info_router.callback_query(F.data == 'try_again_pas')
@user_info_router.message(UpdatePassword.old_pas)
async def set_old_pas(message: Message, state: FSMContext):
    await state.update_data(old_pas=message.text)
    await message.answer(BOT_TEXTS['ask_new_password'],
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=send_cancellation_to_user_info()
                         ),
                         parse_mode='HTML')
    await state.set_state(UpdatePassword.new_pas)


@user_info_router.message(UpdatePassword.new_pas)
async def set_new_pas(message: Message, state: FSMContext):
    await state.update_data(new_pas=message.text)
    await message.answer(BOT_TEXTS['ask_new_password_again'],
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=send_cancellation_to_user_info()
                         ),
                         parse_mode='HTML')
    await state.set_state(UpdatePassword.again_new_pas)


@user_info_router.message(UpdatePassword.again_new_pas)
async def set_again_new_pas(message: Message, state: FSMContext):
    await state.update_data(again_new_pas=message.text)

    data = await state.get_data()
    response = await update_password(data, message.chat.id)
    msg = BOT_TEXTS['password_updated'] if response.get('success') else BOT_TEXTS['generic_error']

    await message.answer(msg,
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=send_profile_to_user_info()
                         ),
                         parse_mode='HTML')
    await state.clear()


@user_info_router.callback_query(F.data == 'change_email')
async def email_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer(BOT_TEXTS['ask_new_email'],
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=send_cancellation_to_user_info()
                              ),
                              parse_mode='HTML')
    await state.set_state(UserInfoStates.change_email)


@user_info_router.message(UserInfoStates.change_email)
async def update_email(message: Message, state: FSMContext):
    response, status = await fetch_post('/change_account_data/email',
                                        {'chat_id': message.chat.id, 'new_email': message.text}
                                        )
    msg = BOT_TEXTS['email_updated'] if status == 200 and response.get('success') else BOT_TEXTS['generic_error']

    await message.answer(msg,
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=send_profile_to_user_info()
                         ),
                         parse_mode='HTML')
    if response.get('success'):
        await state.clear()


@user_info_router.callback_query(F.data == 'change_description')
async def description_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer(BOT_TEXTS['ask_new_description'],
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=send_cancellation_to_user_info()
                              ),
                              parse_mode='HTML')
    await state.set_state(UserInfoStates.change_description)


@user_info_router.message(UserInfoStates.change_description)
async def update_description(message: Message, state: FSMContext):
    response, status = await fetch_post('/change_account_data/description',
                                        {'chat_id': message.chat.id, 'new_description': message.text}
                                        )
    msg = BOT_TEXTS['description_updated'] if status == 200 and response.get('success') else BOT_TEXTS['generic_error']

    await message.answer(msg,
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=send_profile_to_user_info()
                         ),
                         parse_mode='HTML')
    if response.get('success'):
        await state.clear()
