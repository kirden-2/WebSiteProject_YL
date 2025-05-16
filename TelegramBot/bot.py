import asyncio
import logging

from aiogram import Bot, Dispatcher

import TelegramBot.handlers.bot_info as hand_command_list
import TelegramBot.handlers.login as hand_login
import TelegramBot.handlers.register as hand_register
import TelegramBot.handlers.start as hand_start
import TelegramBot.handlers.view_arts as hand_view_arts
import TelegramBot.handlers.user_info as hand_user_info
import TelegramBot.handlers.logout as hand_logout

from TelegramBot.config import BOT_TOKEN
from TelegramBot.utils import init_session, close_session


async def start_bot():
    logging.basicConfig(level=logging.INFO)
    await init_session()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(hand_start.start_router)
    dp.include_router(hand_register.register_route)
    dp.include_router(hand_login.login_router)
    dp.include_router(hand_command_list.bot_info_router)
    dp.include_router(hand_view_arts.view_arts_router)
    dp.include_router(hand_user_info.user_info_router)
    dp.include_router(hand_logout.logout_route)

    try:
        await dp.start_polling(bot)
    finally:
        await close_session()


if __name__ == '__main__':
    asyncio.run(start_bot())
