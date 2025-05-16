from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from TelegramBot.keyboards.inline_kbs import send_start_not_login_kb, send_start_login_kb
from TelegramBot.handlers.login import login_router
from TelegramBot.handlers.register import register_route
from TelegramBot.handlers.view_arts import view_arts_router
from TelegramBot.handlers.user_info import user_info_router

from TelegramBot.check_login import check_user_login_now

from TelegramBot.config import BOT_TEXTS

start_router = Router()


async def send_start(message_obj, chat_id, state: FSMContext):
    await state.clear()
    kb = (
        send_start_login_kb()
        if await check_user_login_now(chat_id)
        else send_start_not_login_kb()
    )

    await message_obj(
        BOT_TEXTS["start_message"],
        reply_markup=kb,
        parse_mode="HTML"
    )


@start_router.message(Command('start'))
@register_route.message(Command('back'))
@view_arts_router.message(Command('back'))
@user_info_router.message(Command('back'))
async def cmd_start_message(message: Message, state: FSMContext):
    await send_start(message.answer, message.chat.id, state)


@login_router.callback_query(F.data == 'back_to_start')
@register_route.callback_query(F.data == 'back_to_start')
@view_arts_router.callback_query(F.data == 'back_to_start')
@user_info_router.callback_query(F.data == 'back_to_start')
async def cmd_start_callback(call: CallbackQuery, state: FSMContext):
    await send_start(call.message.edit_text, call.message.chat.id, state)
