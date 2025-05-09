import logging

from aiogram import Bot, Dispatcher

import Bot.handlers.command_list as hand_command_list
import Bot.handlers.login as hand_login
import Bot.handlers.register as hand_register
import Bot.handlers.start as hand_start
import Bot.handlers.view_arts as hand_view_arts
import Bot.handlers.user_info as hand_user_info

from config import BOT_TOKEN

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()


# Запуск процесса поллинга новых апдейтов
async def start_bot():
    dp.include_router(hand_start.start_router)
    dp.include_router(hand_register.register_route)
    dp.include_router(hand_login.login_router)
    dp.include_router(hand_command_list.command_list_router)
    dp.include_router(hand_view_arts.view_arts_router)
    dp.include_router(hand_user_info.user_info_router)
    await dp.start_polling(bot)