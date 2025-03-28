import asyncio
import logging
from aiogram import Bot, Dispatcher

from Bot.code.handlers.command_list import command_list_router
from Bot.code.handlers.login import login_router
from Bot.code.handlers.register import register_route
from Bot.code.handlers.start import start_router

api = '7658117920:AAElyKWi3joOd8ShIbufmujh0LAM4Mcb3C4'

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=api)
# Диспетчер
dp = Dispatcher()


# Запуск процесса поллинга новых апдейтов
async def main():
    dp.include_router(start_router)
    dp.include_router(register_route)
    dp.include_router(login_router)
    dp.include_router(command_list_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
