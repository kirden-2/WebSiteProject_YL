from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def send_start_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Регистрация", callback_data='register')],
        [InlineKeyboardButton(text="Вход", callback_data='login')],
        [InlineKeyboardButton(text="Осмотреться", callback_data='command_list')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

def send_register_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Почта, Пароль", callback_data='default_reg')],
        [InlineKeyboardButton(text="Аккаунт telegram", callback_data='telegram_reg')],
        [InlineKeyboardButton(text="Вход", callback_data='login')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)

def send_login_kb():
    inline_kb_list = [
        [InlineKeyboardButton(text="Почта, Пароль", callback_data='default_log')],
        [InlineKeyboardButton(text="Аккаунт telegram", callback_data='telegram_log')],
        [InlineKeyboardButton(text="Регистрация", callback_data='register')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)