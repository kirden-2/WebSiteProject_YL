import aiogram.exceptions
from aiogram import F, Router
from aiogram.types import CallbackQuery
from .check_login import check_user_login_now
from ..keyboards.inline_kbs import send_start_not_login_kb, send_start_login_kb

command_list_router = Router()


@command_list_router.callback_query(F.data == 'command_list')
async def command_list(call: CallbackQuery):
    if check_user_login_now(call.message.chat.id):
        kb = send_start_login_kb()
    else:
        kb = send_start_not_login_kb()
    try:
        await call.message.edit_text('Данный бот был создан как альтернатива нашему сайту.\n'
                                     'Здесь вы можете зарегистрироваться, если у вас нет учетной записи,'
                                     ' или же использовать раннее созданную на нашем сайте.\n'
                                     'Просматривайте работы других людей👀, покупайте их 🤑 или же создавайте свои творения!🤩',
                                     reply_markup=kb)
    except aiogram.exceptions.TelegramBadRequest:
        pass
