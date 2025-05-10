import asyncio
import aiogram
from aiogram import F, Router, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from Bot.keyboards.inline_kbs import send_view_art_kb, send_view_continue_kb, send_cancel_kb
from Bot.handlers.check_login import check_user_login_now

from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.media_group import MediaGroupBuilder

from config import SITE_API

import requests

view_arts_router = Router()


def check_art_data(data):
    title = data["title"]
    price = data["price"]

    if not title or not price:
        return 'Не все данные заполнены'
    if '.' in price:
        return 'Цена должна являться целым числом'
    try:
        price = int(price)
    except Exception:
        return 'Цена должна являться целым числом'
    return 'OK'


class ViewForm(StatesGroup):
    ViewArtWithId = State()


class ArtData(StatesGroup):
    image = State()
    title = State()
    description = State()
    short_description = State()
    price = State()


@view_arts_router.callback_query(F.data == 'view_menu')
@view_arts_router.callback_query(F.data == 'cancel_create')
async def view_menu(call: CallbackQuery):
    await call.message.edit_text('Вы можете просмотреть работу, указав её id, или же просмотреть случайную работу',
                                 reply_markup=send_view_art_kb(login=check_user_login_now(call.message.chat.id)))
    await call.answer()


@view_arts_router.callback_query(F.data == 'view_random_art')
async def view_random_art(message: CallbackQuery, state: FSMContext):
    await message.message.answer('Подбираем работу, это может занять некоторое время...')
    await asyncio.sleep(1)
    try:
        req = requests.post(
            f'{SITE_API}/arts/random_art',
            json={'chat_id': message.message.chat.id}
        ).json()
        async with ChatActionSender.upload_photo(bot=message.message.bot, chat_id=message.message.chat.id):
            # Создаем медиа группу для картинок
            media = MediaGroupBuilder()
            media.add_photo(FSInputFile(f'WebSite/static/img/arts/{req["art"]["id"]}{req["art"]["extension"]}'),
                            caption=f'''Случайная работа\n
💡Название: {req["art"]["name"]}\n
🏷️id работы: {req["art"]["id"]}\n
🔈Описание работы(кратко): {req["art"]["short_description"] if req["art"]["short_description"] else 'описание отсутствует'}\n
👨‍💻Создатель: {req["art"]["creator"] if req["art"]["creator"] else 'не указан'}\n
🏆Обладатель: {req["art"]["owner"] if req["art"]["owner"] else 'не указан'}\n
💵Цена: {f'{req["art"]["price"]} Digital Coins' if req["art"]["price"] else 'не указана'}\n
👁️Просмотры: {req["art"]["views"] if req["art"]["views"] else 'не указаны'}\n
⏱️Дата создания: {req["art"]["creation_time"] if req["art"]["creation_time"] else 'не указана'}\n
''')
        await asyncio.sleep(1)
        await message.message.answer_media_group(media=media.build())
        await state.update_data(art_id=req["art"]["id"])
        await message.message.answer('Если вам понравилась работа, вы можете её приобрести',
                                     reply_markup=send_view_continue_kb())
    except aiogram.exceptions.TelegramBadRequest:
        await message.message.answer(
            f'Не удалось отобразить работу. Изображение занимает слишком большой размер памяти.',
            reply_markup=send_view_continue_kb(error=True))

    except Exception:
        await message.message.answer(f'Произошла ошибка. Попробуйте еще раз',
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
        req = requests.post(
            f'{SITE_API}/arts/{message.text}',
            json={'chat_id': message.chat.id}
        ).json()
        async with ChatActionSender.upload_photo(bot=message.bot, chat_id=message.chat.id):
            # Создаем медиа группу для картинок
            media = MediaGroupBuilder()
            media.add_photo(FSInputFile(f'WebSite/static/img/arts/{req["art"]["id"]}{req["art"]["extension"]}'),
                            caption=f'''Работа по запросу\n
💡Название: {req["art"]["name"]}\n
🏷️id работы: {req["art"]["id"]}\n
🔈Описание работы(кратко): {req["art"]["short_description"] if req["art"]["short_description"] else 'описание отсутствует'}\n
👨‍💻Создатель: {req["art"]["creator"] if req["art"]["creator"] else 'не указан'}\n
🏆Обладатель: {req["art"]["owner"] if req["art"]["owner"] else 'не указан'}\n
💵Цена: {f'{req["art"]["price"]} Digital Coins' if req["art"]["price"] else 'не указана'}\n
👁️Просмотры: {req["art"]["views"] if req["art"]["views"] else 'не указаны'}\n
⏱️Дата создания: {req["art"]["creation_time"] if req["art"]["creation_time"] else 'не указана'}\n
''')
        await asyncio.sleep(1)
        await message.answer_media_group(media=media.build())
        await state.update_data(art_id=req["art"]["id"])
        await message.answer('Если вам понравилась работа, вы можете её приобрести',
                             reply_markup=send_view_continue_kb())
    except Exception:
        await message.answer(f'{req["error"]}. Попробуйте еще раз',
                             reply_markup=send_view_continue_kb(error=True))


@view_arts_router.callback_query(F.data == 'skip')
async def view_continue(call: CallbackQuery):
    await call.message.answer('Желаете продолжить?',
                              reply_markup=send_view_art_kb(login=check_user_login_now(call.message.chat.id)))


@view_arts_router.callback_query(F.data == 'purchase_artwork')
async def purchase(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    response = requests.post(f'{SITE_API}/purchase/{data["art_id"]}',
                             json={'chat_id': call.message.chat.id}).json()
    try:
        if not check_user_login_now(call.message.chat.id):
            raise PermissionError
        if response["success"]:
            await call.message.answer(f'{response["success"]}')
    except KeyError or IndexError:
        await call.message.answer(f'{response["error"]}', reply_markup=send_view_continue_kb(error=True))
    except PermissionError:
        await call.message.answer('Для совершения покупки необходимо авторизоваться',
                                  reply_markup=send_view_continue_kb(error=True))


@view_arts_router.callback_query(F.data == 'create_art')
async def set_image(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Для создания собственной работы отправьте изображение в чат\n'
                              '(Поддерживаемые форматы: png, jpg, jpeg)',
                              reply_markup=send_cancel_kb())
    await state.set_state(ArtData.image)


@view_arts_router.message(lambda message: message.photo)
async def set_title(message: Message, state: FSMContext):
    await state.update_data(image=message.photo[-1])
    await message.answer('Укажите название')
    await state.set_state(ArtData.title)


@view_arts_router.message(ArtData.title)
async def set_description(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer('Укажите описание')
    await state.set_state(ArtData.description)


@view_arts_router.message(ArtData.description)
async def set_short_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Укажите краткое описание')
    await state.set_state(ArtData.short_description)


@view_arts_router.message(ArtData.short_description)
async def set_price(message: Message, state: FSMContext):
    await state.update_data(short_description=message.text)
    await state.update_data(description=message.text)
    await message.answer('Укажите цену в Digital Coins (целое число)')
    await state.set_state(ArtData.price)


@view_arts_router.message(ArtData.price)
async def add_art(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(price=message.text)
    user_data = await state.get_data()
    checking_res = check_art_data(user_data)
    if checking_res == 'OK':
        response = requests.post(f'{SITE_API}/arts/add_artwork',
                                 json={'title': user_data["title"], 'description': user_data["description"],
                                       'short_description': user_data["short_description"], 'price': user_data["price"],
                                       'image': user_data["image"].file_id, 'chat_id': message.chat.id}).json()
        if response['success']:
            file = await bot.get_file(user_data["image"].file_id)
            await bot.download_file(file.file_path, f'./WebSite/static/img/arts/{response["art_id"]}.jpg')
            await message.answer(f'Работа была успешно добавлена в каталог. Присвоенное id: {response["art_id"]}',
                                 reply_markup=send_view_art_kb(login=True))
            await state.set_state(None)
    else:
        await message.answer(checking_res)


@view_arts_router.callback_query(F.data == 'owned_arts')
async def view_owned_arts(call: CallbackQuery):
    response = requests.get(f'{SITE_API}/arts', json={'chat_id': call.message.chat.id}).json()
    if response["arts"]:
        await call.message.answer(f'Список работ, которыми вы обладаете(всего {len(response["arts"])}):')
        for art in response["arts"]:
            await asyncio.sleep(0.5)
            await call.message.answer(f'Название: {art["name"]}; id: {art["id"]}')
    else:
        await call.message.answer('На данный момент вам не принадлежит ни одна работа')
