import asyncio

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from Bot.code.keyboards.inline_kbs import send_view_art_kb, send_view_continue_kb

from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.media_group import MediaGroupBuilder

from ..config import SITE_API

import requests

view_arts_router = Router()


class ViewForm(StatesGroup):
    ViewArtWithId = State()


@view_arts_router.callback_query(F.data == 'view_menu')
async def view_menu(call: CallbackQuery):
    await call.message.edit_text('Вы можете просмотреть работу, указав её id, или же просмотреть случайную работу',
                                 reply_markup=send_view_art_kb())
    await call.answer()


@view_arts_router.callback_query(F.data == 'view_random_art')
async def view_random_art(message: CallbackQuery):
    await message.message.answer('Подбираем работу, это может занять некоторое время...')
    await asyncio.sleep(1)
    try:
        req = requests.get(f'{SITE_API}/arts/random_art').json()
        async with ChatActionSender.upload_photo(bot=message.message.bot, chat_id=message.message.chat.id):
            # Создаем медиа группу для картинок
            media = MediaGroupBuilder()
            media.add_photo(FSInputFile(f'WebSite/static/img/{req["art"]["id"]}{req["art"]["extension"]}'),
                            caption=f'''Случайная работа\n
💡Название: {req["art"]["name"]}\n
🏷️id работы: {req["art"]["id"]}\n
🔈Описание работы(кратко): {req["art"]["short_description"] if req["art"]["short_description"] else 'описание отсутствует'}\n
👨‍💻Создатель: {req["art"]["creator"] if req["art"]["creator"] else 'не указан'}\n
🏆Обладатель: {req["art"]["owner"] if req["art"]["owner"] else 'не указан'}\n
💵Цена: {f'{req["art"]["price"]} ETH♢' if req["art"]["price"] else 'не указана'}\n
👁️Просмотры: {req["art"]["views"] if req["art"]["views"] else 'не указаны'}\n
⏱️Дата создания: {req["art"]["creation_time"] if req["art"]["creation_time"] else 'не указана'}\n
''')
        await asyncio.sleep(1)
        await message.message.answer_media_group(media=media.build())
        await message.message.answer('Если вам понравилась работа, вы можете её приобрести',
                                     reply_markup=send_view_continue_kb())
    except Exception:
        await message.message.answer('Произошла ошибка. Попробуйте еще раз',
                                     reply_markup=send_view_continue_kb(error=True))


@view_arts_router.callback_query(F.data == 'view_art_with_id')
async def get_art_id(call: CallbackQuery, state: FSMContext):
    await state.set_state(ViewForm.ViewArtWithId)
    await call.message.answer('Введите id интересующей вас работы')


@view_arts_router.message(ViewForm.ViewArtWithId)
async def view_art_with_id(message: Message, state: FSMContext):
    await message.answer('Ищем нужную работу, это может занять некоторое время...')
    await asyncio.sleep(1)
    await state.set_state(None)
    try:
        req = requests.get(f'{SITE_API}/arts/{message.text}').json()
        async with ChatActionSender.upload_photo(bot=message.bot, chat_id=message.chat.id):
            # Создаем медиа группу для картинок
            media = MediaGroupBuilder()
            media.add_photo(FSInputFile(f'WebSite/static/img/{req["art"]["id"]}{req["art"]["extension"]}'),
                            caption=f'''Работа по запросу\n
💡Название: {req["art"]["name"]}\n
🏷️id работы: {req["art"]["id"]}\n
🔈Описание работы(кратко): {req["art"]["short_description"] if req["art"]["short_description"] else 'описание отсутствует'}\n
👨‍💻Создатель: {req["art"]["creator"] if req["art"]["creator"] else 'не указан'}\n
🏆Обладатель: {req["art"]["owner"] if req["art"]["owner"] else 'не указан'}\n
💵Цена: {f'{req["art"]["price"]} ETH♢' if req["art"]["price"] else 'не указана'}\n
👁️Просмотры: {req["art"]["views"] if req["art"]["views"] else 'не указаны'}\n
⏱️Дата создания: {req["art"]["creation_time"] if req["art"]["creation_time"] else 'не указана'}\n
''')
        await asyncio.sleep(1)
        await message.answer_media_group(media=media.build())
        await message.answer('Если вам понравилась работа, вы можете её приобрести',
                             reply_markup=send_view_continue_kb())
    except Exception:
        await message.answer(f'{req["error"]}. Попробуйте еще раз',
                             reply_markup=send_view_continue_kb(error=True))


@view_arts_router.callback_query(F.data == 'skip')
async def view_continue(call: CallbackQuery):
    await call.message.answer('Желаете продолжить?', reply_markup=send_view_art_kb())


@view_arts_router.callback_query(F.data == 'purchase_artwork')
async def purchase(call: CallbackQuery):
    await call.message.answer('Эта функция пока не доступна')
