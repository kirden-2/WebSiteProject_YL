from aiogram import F, Router
from aiogram.types import CallbackQuery
from TelegramBot.check_login import check_user_login_now
from TelegramBot.keyboards.inline_kbs import send_start_not_login_kb, send_start_login_kb
from TelegramBot.config import BOT_TEXTS

bot_info_router = Router()


@bot_info_router.callback_query(F.data == 'bot_info')
async def bot_info(call: CallbackQuery):
    await call.message.edit_text(BOT_TEXTS['bot_info_message'],
                                 reply_markup=send_start_login_kb() if await check_user_login_now(
                                     call.message.chat.id) else send_start_not_login_kb(),
                                 parse_mode="HTML")
