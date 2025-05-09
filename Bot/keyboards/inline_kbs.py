from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram_dialog.widgets.kbd import Url, Button
from aiogram_dialog.widgets.text import Const


def send_start_not_login_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Регистрация", callback_data='register'),
         InlineKeyboardButton(text="Вход", callback_data='login')],
        [InlineKeyboardButton(text="Перейти к NFT", callback_data='view_menu')],
        [InlineKeyboardButton(text="Возможности нашего бота", callback_data='command_list')],
        [InlineKeyboardButton(text="Digital Gallery", url='http://127.0.0.1:5000/')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_start_login_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Перейти к NFT", callback_data='view_menu')],
        [InlineKeyboardButton(text="Информация об учетной записи", callback_data='user_info')],
        [InlineKeyboardButton(text="Возможности нашего бота", callback_data='command_list')],
        [InlineKeyboardButton(text="Выйти из учетной записи", callback_data='logout')],
        [InlineKeyboardButton(text="Digital Gallery", url='http://127.0.0.1:5000/')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_register_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Стандартная регистрация", callback_data='default_reg')],
        [InlineKeyboardButton(text="Аккаунт telegram", callback_data='telegram_reg')],
        [InlineKeyboardButton(text="Вход", callback_data='login'),
         InlineKeyboardButton(text='Вернуться', callback_data='back_to_start')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_confirm_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Продолжить", callback_data='continue_tg_reg')],
        [InlineKeyboardButton(text="Отмена", callback_data='cancel')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_login_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Стандартная авторизация", callback_data='default_log')],
        [InlineKeyboardButton(text="Аккаунт telegram", callback_data='telegram_log')],
        [InlineKeyboardButton(text="Регистрация", callback_data='register'),
         InlineKeyboardButton(text="Вернуться", callback_data='back_to_start')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_cancel_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Вернуться", message_data='return_to_start', callback_data='back_to_start')]]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_retry_reg_kb():
    inline_kb_list = [[InlineKeyboardButton(text="Повторить попытку", callback_data='register')]]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_retry_login_kb():
    inline_kb_list = [[InlineKeyboardButton(text="Повторить попытку", callback_data='login')]]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_view_art_kb():
    inline_kb_list = [[InlineKeyboardButton(text="Указать id работы", callback_data='view_art_with_id')],
                      [InlineKeyboardButton(text="Просмотреть случайную работу", callback_data='view_random_art')],
                      [InlineKeyboardButton(text="Вернуться", callback_data='back_to_start')]]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_view_continue_kb(error=False):
    if not error:
        inline_kb_list = [[InlineKeyboardButton(text="Купить показанную работу", callback_data='purchase_artwork')],
                          [InlineKeyboardButton(text="Пропустить", callback_data='skip')]]
    else:
        inline_kb_list = [[InlineKeyboardButton(text="Пропустить", callback_data='skip')]]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_change_account_data_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Сменить пароль", callback_data='change_password')],
        [InlineKeyboardButton(text="Сменить email", callback_data='change_email')],
        [InlineKeyboardButton(text="Сменить описание профиля", callback_data='change_description')],
        [InlineKeyboardButton(text="Вернуться", callback_data='back_to_start')]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)
