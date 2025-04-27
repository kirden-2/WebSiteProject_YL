from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.filters import Command
from aiogram_dialog.widgets.kbd import Url, Button
from aiogram_dialog.widgets.text import Const


def send_start_not_login_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Регистрация", callback_data='register'),
         InlineKeyboardButton(text="Вход", callback_data='login')],
        [InlineKeyboardButton(text="Перейти к NFT", callback_data='view_menu')],
        [InlineKeyboardButton(text="Список команд", callback_data='command_list')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def send_start_login_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Перейти к NFT", callback_data='view_menu')],
        [InlineKeyboardButton(text="Список команд", callback_data='command_list')]
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
