from aiogram import F, Router
from aiogram.types import CallbackQuery

from Bot.code.keyboards.inline_kbs import send_register_kb

register_route = Router()

@register_route.callback_query(F.data == 'register')
async def register(call: CallbackQuery):
    await call.message.edit_text('Выберете подходящий для вас способ регистрации', reply_markup=send_register_kb())
    await call.answer()