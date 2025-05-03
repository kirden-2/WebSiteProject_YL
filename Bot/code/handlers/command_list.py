from aiogram import F, Router
from aiogram.types import CallbackQuery

command_list_router = Router()


@command_list_router.callback_query(F.data == 'command_list')
async def command_list(call: CallbackQuery):
    await call.message.answer('Данный бот был создан как альтернатива нашему сайту.\n'
                              'Здесь вы можете зарегистрироваться, если у вас нету учетной записи'
                              ' или же использовать ранне созданную с нашего сайта.\n'
                              'Просматривайте работы других людей, покупайте их или же создавайте свои творения!🤩')
