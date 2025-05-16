from aiogram import Router, F
from aiogram.types import CallbackQuery

from TelegramBot.keyboards.inline_kbs import send_start_not_login_kb, send_start_login_kb
from TelegramBot.utils import fetch_post
from TelegramBot.config import BOT_TEXTS

logout_route = Router()


@logout_route.callback_query(F.data == 'logout')
async def logout(call: CallbackQuery):
    response, status = await fetch_post('/logout',
                                        {'chat_id': call.message.chat.id}
                                        )

    if status == 200 and response.get('success'):
        await call.message.edit_text(BOT_TEXTS["start_message"],
                                     reply_markup=send_start_not_login_kb(),
                                     parse_mode="HTML")
    else:
        await call.message.edit_text(response.get('user_message', BOT_TEXTS["generic_error"]),
                                     reply_markup=send_start_login_kb(),
                                     parse_mode="HTML")
