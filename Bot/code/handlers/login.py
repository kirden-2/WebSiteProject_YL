from aiogram import F, Router
from aiogram.types import CallbackQuery

from Bot.code.keyboards.inline_kbs import send_login_kb

login_router = Router()


@login_router.callback_query(F.data == 'login')
async def login(call: CallbackQuery):
    await call.message.edit_text('Выберете подходящий способ авторизации', reply_markup=send_login_kb())
    await call.answer()
