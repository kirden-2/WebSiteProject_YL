from aiogram import F, Router
from aiogram.types import CallbackQuery

account_router = Router()


@account_router.callback_query(F.data == 'account')
async def account(call: CallbackQuery):
    await call.message.answer('')
