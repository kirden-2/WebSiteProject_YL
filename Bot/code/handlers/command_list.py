from aiogram import F, Router
from aiogram.types import CallbackQuery

command_list_router = Router()


@command_list_router.callback_query(F.data == 'command_list')
async def command_list(call: CallbackQuery):
    await call.message.answer('Команды нашего бота:\n'
                              '/account - посмотреть свой профиль\n'
                              '/register - зарегистрироваться'
                              '/login - авторизоваться\n'
                              '/look - посмотреть чей-то профиль')