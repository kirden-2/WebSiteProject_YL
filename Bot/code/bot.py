import asyncio
import logging
import os

import aiogram.fsm.context
from aiogram import Bot, Dispatcher, F, Router

from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import Bot.code.handlers.command_list as hand_command_list
import Bot.code.handlers.login as hand_login
import Bot.code.handlers.register as hand_register
import Bot.code.handlers.start as hand_start
import Bot.code.handlers.view_arts as hand_view_arts

api = ''

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=api)
# Диспетчер
dp = Dispatcher()


# Запуск процесса поллинга новых апдейтов
async def main():
    dp.include_router(hand_start.start_router)
    dp.include_router(hand_register.register_route)
    dp.include_router(hand_login.login_router)
    dp.include_router(hand_command_list.command_list_router)
    dp.include_router(hand_view_arts.view_arts_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    os.chdir('..')
    os.chdir('..')
    asyncio.run(main())
