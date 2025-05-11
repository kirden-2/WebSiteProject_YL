import requests
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from Bot.keyboards.inline_kbs import send_change_account_data_kb, send_start_login_kb
from config import SITE_API

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
    old_pas = data.get('old_pas', '')
    new_pas = data.get('new_pas', '')
    again_new_pas = data.get('again_new_pas', '')
    try:
        response = requests.put(f'{SITE_API}/change_account_data/password',
                                json={'chat_id': chat_id,
                                      'old_password': old_pas,
                                      'new_password': new_pas,
                                      'again_new_password': again_new_pas}
                                ).json()
    except requests.RequestException:
        return {'success': False, 'error': 'Не удалось связаться с сервером, попробуйте позже'}
    return response


@user_info_router.callback_query(F.data == 'user_info')
async def get_user_info(call: CallbackQuery, state: FSMContext):
    await state.clear()
    chat_id = call.message.chat.id
    try:
        response = requests.post(f'{SITE_API}/user_info',
                                 json={'chat_id': chat_id}
                                 ).json()
    except requests.RequestException:
        await call.message.edit_text('Не удалось связаться с сервером, попробуйте позже',
                                     reply_markup=send_start_login_kb())
        return

    if response.get('success', ''):
        await call.message.edit_text(
            f'''Информация о {response["user"]["nick_name"]}:

️🏷️id пользователя: {response["user"]["id"]}
📧email: {response["user"]["email"] if response["user"]["email"] else "не указан"}
✏️Описание профиля: {response["user"]["description"] if response["user"]["description"] else "не указано"}
💰Баланс: {response["user"]["balance"]}
🗓️Дата создания аккаунта: {response["user"]["creation_time"]}''',
            reply_markup=send_change_account_data_kb()
        )
    else:
        error = response.get('error', 'Неизвестная ошибка')
        await call.message.edit(f'Ошибка: {error}',
                                reply_markup=send_change_account_data_kb()
                                )


@user_info_router.callback_query(F.data == 'change_password')
async def password_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Введите текущий пароль',
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=[
                                      [InlineKeyboardButton(text="Отмена", callback_data='user_info')]]))
    await state.set_state(UpdatePassword.old_pas)


@user_info_router.callback_query(F.data == 'try_again_pas')
@user_info_router.message(UpdatePassword.old_pas)
async def set_old_pas(message: Message, state: FSMContext):
    await state.update_data(old_pas=message.text)
    await message.answer('Введите новый пароль',
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [InlineKeyboardButton(text="Отмена", callback_data='user_info')]])
                         )
    await state.set_state(UpdatePassword.new_pas)


@user_info_router.message(UpdatePassword.new_pas)
async def set_new_pas(message: Message, state: FSMContext):
    await state.update_data(new_pas=message.text)
    await message.answer('Повторите новый пароль',
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [InlineKeyboardButton(text="Отмена", callback_data='user_info')]])
                         )
    await state.set_state(UpdatePassword.again_new_pas)


@user_info_router.message(UpdatePassword.again_new_pas)
async def set_again_new_pas(message: Message, state: FSMContext):
    await state.update_data(again_new_pas=message.text)

    data = await state.get_data()
    res = await update_password(data, message.chat.id)
    if res.get('success', ''):
        mes = 'Пароль успешно обновлён'
    else:
        error = res.get('error', 'Неизвестная ошибка')
        mes = f'Ошибка: {error}'
    await message.answer(mes,
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[[InlineKeyboardButton(text="Профиль", callback_data='user_info')]]))
    await state.clear()


@user_info_router.callback_query(F.data == 'change_email')
async def email_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Введите новую почту',
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=[
                                      [InlineKeyboardButton(text="Отмена", callback_data='user_info')]])
                              )
    await state.set_state(UserInfoStates.change_email)


@user_info_router.message(UserInfoStates.change_email)
async def update_email(message: Message, state: FSMContext):
    try:
        response = requests.put(f'{SITE_API}/change_account_data/email',
                                json={'chat_id': message.chat.id,
                                      'new_email': message.text}).json()
    except requests.RequestException:
        await message.answer('Не удалось связаться с сервером, попробуйте позже')
        return

    if response.get('success', ''):
        await message.answer('Почта успешно изменена',
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[[InlineKeyboardButton(text="Профиль", callback_data='user_info')]])
                             )
        await state.clear()
    else:
        error = response.get('error', 'Неизвестная ошибка')
        await message.answer(f'Ошибка: {error}\nВведите почту заново',
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text="Отмена", callback_data='user_info')]])
                             )


@user_info_router.callback_query(F.data == 'change_description')
async def description_confirm(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Введите новое описание вашего профиля',
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=[
                                      [InlineKeyboardButton(text="Отмена", callback_data='user_info')]])
                              )
    await state.set_state(UserInfoStates.change_description)


@user_info_router.message(UserInfoStates.change_description)
async def update_description(message: Message, state: FSMContext):
    try:
        response = requests.put(f'{SITE_API}/change_account_data/description',
                                json={'chat_id': message.chat.id,
                                      'new_description': message.text}).json()
    except requests.RequestException:
        await message.answer('Не удалось связаться с сервером. Попробуйте позже.')
        return

    if response.get('success', ''):
        await message.answer('Описание профиля успешно изменено',
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[[InlineKeyboardButton(text="Профиль", callback_data='user_info')]])
                             )
        await state.clear()
    else:
        error = response.get('error', 'Неизвестная ошибка')
        await message.answer(f'Ошибка: {error}\nВведите описание заново',
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text="Отмена", callback_data='user_info')]])
                             )
