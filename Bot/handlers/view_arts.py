import asyncio
import mimetypes

import aiogram
from aiogram import F, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiohttp import ClientSession, FormData
import Bot.bot
from Bot.keyboards.inline_kbs import send_view_art_kb, send_cancel_kb, send_art_kb
from Bot.handlers.check_login import check_user_login_now

from aiogram.utils.chat_action import ChatActionSender

from config import SITE_API, ALLOWED_EXTENSIONS


view_arts_router = Router()


class ViewArt(StatesGroup):
    get_id = State()


class SendOwnedArts(StatesGroup):
    arts = State()


class ArtData(StatesGroup):
    image = State()
    title = State()
    description = State()
    short_description = State()
    category = State()
    price = State()


def get_value(data, key, max_len=None):
    val = data.get(key, 'Не удалось найти')
    text = str(val)
    if max_len and len(text) > max_len:
        return text[:max_len - 3] + '..'
    return text


def build_caption(art):
    lines = [
        f"{get_value(art, 'name', max_len=500)}",
        f"🏷️ ID: {get_value(art, 'id')}",
        f"🔈 Описание: {get_value(art, 'short_description', max_len=3000)}",
        f"👨‍💻 Творец: {get_value(art, 'creator', max_len=100)}",
        f"🏆 Обладатель: {get_value(art, 'owner', max_len=100)}",
    ]

    price = art.get('price', None)
    if price is None or price <= 0:
        lines.append("💵 Цена: Не продаётся")
    else:
        lines.append(f"💵 Цена: {price} Digital Coins")

    views = art.get('views', 'Не удалось найти')
    lines.append(f"👁 Просмотры: {views}")

    creation = art.get('creation_time', 'Не удалось найти')
    lines.append(f"⏱ Дата создания: {creation}")

    return '\n'.join(lines)


async def get_art(chat_id, endpoint):
    session = Bot.bot.session
    if not isinstance(session, ClientSession):
        return {'success': False, 'error': 'Сетевая сессия не инициализирована. Попробуйте позже.'}, 500

    try:
        response, status = await fetch_post(session, endpoint, {"chat_id": chat_id})
    except Exception:
        return {'success': False, 'error': 'Не удалось связаться с сервером. Попробуйте позже.'}, 500
    return response, status


async def fetch_post(session, endpoint, payload, file_bytes=None, field_name='file', filename=None, content_type=None):
    url = f"{SITE_API}{endpoint}"

    if file_bytes is not None:
        form = FormData()
        for key, value in payload.items():
            form.add_field(key, str(value))
        form.add_field(
            field_name,
            file_bytes,
            filename=filename,
            content_type=content_type,
        )
        async with session.post(url, data=form) as resp:
            return await resp.json(), resp.status
    else:
        async with session.post(url, json=payload) as resp:
            return await resp.json(), resp.status


async def add_art(message, state, bot):
    data = await state.get_data()

    session = Bot.bot.session
    file_id = data["image"].file_id
    file_info = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file_info.file_path)

    filename = file_info.file_path.rsplit('/', 1)[-1]

    if filename.lower().endswith(ALLOWED_EXTENSIONS):
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            if filename.lower().endswith('.gif'):
                mime_type = 'image/gif'
    else:
        await message.answer(f'Не поддерживаемый формат файла. Попробуйте снова.',
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text="Повторить", callback_data='create_art')]
                                 ]
                             ))
        return

    try:
        response, status = await fetch_post(session, '/arts/add_artwork',
                                            {'title': data.get('title', ''), 'description': data.get('description', ''),
                                             'short_description': data.get('short_description', ''),
                                             'price': data.get('price', ''), 'chat_id': message.chat.id},
                                            file_bytes=file_bytes.getvalue(),
                                            field_name='image',
                                            filename=filename,
                                            content_type=mime_type
                                            )
    except Exception:
        await message.answer('Не удалось связаться с сервером. Попробуйте позже.',
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text="Меню", callback_data='view_menu')]
                                 ]
                             ))
        return

    if status == 200 and response.get('success', False):
        await message.answer(f'Работа успешно сохранена. id - {response.get('art_id', 'не удалось получить')}',
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text="Меню", callback_data='view_menu')]
                                 ]
                             ))


@view_arts_router.callback_query(F.data == 'view_menu')
async def view_menu(call: CallbackQuery):
    text = 'Вы можете просмотреть работу, указав её id, или же просмотреть случайную работу'
    reply_markup = send_view_art_kb(login=check_user_login_now(call.message.chat.id))

    try:
        await call.message.edit_text(text=text, reply_markup=reply_markup)
    except aiogram.exceptions.TelegramBadRequest:
        await call.message.answer(text=text, reply_markup=reply_markup)

    await call.answer()


@view_arts_router.callback_query(F.data == 'view_random_art')
async def view_random_art(call: CallbackQuery):
    msg = await call.message.answer('Подбираем работу, это может занять некоторое время...')
    bot = call.bot
    response, status = await get_art(call.message.chat.id, '/arts')

    if status == 200 and response.get('success', False):
        try:
            async with ChatActionSender.upload_photo(
                    bot=bot,
                    chat_id=call.message.chat.id
            ):
                art = response.get('art', {})
                caption = build_caption(art)
                path = f'WebSite/static/img/arts/{art["id"]}{art["extension"]}'
                file = FSInputFile(path)

                if art["extension"].lower() == '.gif':
                    await call.message.answer_animation(
                        animation=file,
                        caption=caption,
                        reply_markup=send_art_kb(art.get('id', None),
                                                 bool(art.get('owner_chat_id', '') == call.message.chat.id), True)
                    )
                else:
                    await call.message.answer_photo(
                        photo=file,
                        caption=caption,
                        reply_markup=send_art_kb(art.get('id', None),
                                                 bool(art.get('owner_chat_id', '') == call.message.chat.id), True)
                    )
        except TelegramBadRequest as e:
            err = (e.message or "").lower()
            if 'too big' in err:
                text = 'Не удалось отправить изображение — слишком большой размер.'
            else:
                text = 'Не удалось отобразить работу, попробуйте снова.'
            await call.message.answer(text,
                                      reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                          [InlineKeyboardButton(text="Повторить", callback_data='view_random_art')]
                                      ]))

    else:
        rm = InlineKeyboardMarkup(inline_keyboard=[])
        if status == 500:
            rm.inline_keyboard.append([InlineKeyboardButton(text="Меню", callback_data='view_menu')])
        else:
            rm.inline_keyboard.append([InlineKeyboardButton(text="Повторить", callback_data='view_random_art')])

        await call.message.answer(f"Ошибка: {response.get('error', 'Неизвестная ошибка. Повторите запрос позже.')}",
                                  reply_markup=rm)
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)


@view_arts_router.callback_query(F.data == 'view_art_with_id')
async def get_art_id(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Режим поиска по id\n'
                              'Вводите id интересующей вас работы, чтобы получить её')
    await state.set_state(ViewArt.get_id)


@view_arts_router.message(ViewArt.get_id)
async def view_art_with_id(message: Message):
    msg = await message.answer('Ищем нужную работу, это может занять некоторое время...')
    bot = message.bot
    response, status = await get_art(message.chat.id, f'/arts/{message.text}')

    if status == 200 and response.get('success', False):
        try:
            async with ChatActionSender.upload_photo(
                    bot=bot,
                    chat_id=message.chat.id
            ):
                art = response.get('art', {})
                caption = build_caption(art)
                path = f'WebSite/static/img/arts/{art["id"]}{art["extension"]}'
                file = FSInputFile(path)

                if art["extension"].lower() == '.gif':
                    await message.answer_animation(
                        animation=file,
                        caption=caption,
                        reply_markup=send_art_kb(art.get('id', None),
                                                 bool(art.get('owner_chat_id', '') == message.chat.id), False)
                    )
                else:
                    await message.answer_photo(
                        photo=file,
                        caption=caption,
                        reply_markup=send_art_kb(art.get('id', None),
                                                 bool(art.get('owner_chat_id', '') == message.chat.id), False)
                    )
        except TelegramBadRequest as e:
            err = (e.message or "").lower()
            if 'too big' in err:
                text = 'Не удалось отправить изображение — слишком большой размер.'
            else:
                text = 'Не удалось отобразить работу, попробуйте снова.'
            await message.answer(text,
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                     [InlineKeyboardButton(text="Повторить", callback_data='view_art_with_id')]
                                 ]))

    else:
        rm = InlineKeyboardMarkup(inline_keyboard=[])
        if status == 500:
            rm.inline_keyboard.append([InlineKeyboardButton(text="Меню", callback_data='view_menu')])
        else:
            rm.inline_keyboard.append([InlineKeyboardButton(text="Повторить", callback_data='view_art_with_id')])

        await message.answer(f"Ошибка: {response.get('error', 'Неизвестная ошибка. Повторите запрос позже.')}",
                             reply_markup=rm)
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)


@view_arts_router.callback_query(lambda c: c.data.startswith('purchase_artwork'))
async def check_purchase(call: CallbackQuery):
    art_id = call.data.split('_')[-1]
    await call.message.answer(f'Подтвердите покупку работы {art_id}',
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=[
                                      [InlineKeyboardButton(text="Подтверждаю",
                                                            callback_data=f'continue_purchase_{art_id}')],
                                      [InlineKeyboardButton(text="Отмена", callback_data=f'view_menu')]
                                  ]
                              ))


@view_arts_router.callback_query(lambda c: c.data.startswith('continue_purchase_'))
async def purchase(call: CallbackQuery):
    art_id = call.data.split('_')[-1]
    response, status = await get_art(call.message.chat.id, f'/purchase/{art_id}')
    try:
        if not check_user_login_now(call.message.chat.id):
            raise PermissionError
        if status == 200 and response.get('success', False):
            await call.message.answer(f'Работа {art_id} успешно приобретена!')
    except Exception:
        await call.message.answer(f'Произошла ошибка, попробуйте купить работу позже',
                                  reply_markup=InlineKeyboardMarkup(
                                      inline_keyboard=[
                                          [InlineKeyboardButton(text="Меню", callback_data='view_menu')]
                                      ]
                                  ))
    except PermissionError:
        await call.message.answer('Для совершения покупки необходимо авторизоваться',
                                  reply_markup=InlineKeyboardMarkup(
                                      inline_keyboard=[
                                          [InlineKeyboardButton(text="Меню", callback_data='view_menu')]
                                      ]
                                  ))


@view_arts_router.callback_query(F.data == 'create_art')
async def set_image(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Для создания собственной работы отправьте её в чат\n'
                              '(Поддерживаемые форматы: png, jpg, jpeg, gif)',
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
    await message.answer('Укажите описание\n"нет" для пропуска')
    await state.set_state(ArtData.description)


@view_arts_router.message(ArtData.description)
async def set_short_description(message: Message, state: FSMContext):
    if message.text.lower() != 'нет':
        await state.update_data(description=message.text)
    await message.answer('Укажите краткое описание\n"нет" для пропуска')
    await state.set_state(ArtData.short_description)


@view_arts_router.message(ArtData.short_description)
async def set_price(message: Message, state: FSMContext):
    if message.text.lower() != 'нет':
        await state.update_data(short_description=message.text)
    await message.answer('Укажите категорию работы\nесли их несколько, то укажите каждую через запятую')
    await state.set_state(ArtData.category)


@view_arts_router.message(ArtData.category)
async def set_short_description(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer('Укажите цену в Digital Coins (целое число)')
    await state.set_state(ArtData.short_description)


@view_arts_router.message(ArtData.price)
async def set_price(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(price=message.text)
    await add_art(message, state, bot)


@view_arts_router.callback_query(F.data == 'owned_arts')
async def view_owned_arts(call: CallbackQuery, state: FSMContext):
    response, status = await get_art(call.message.chat.id, '/owned_arts')
    try:
        if status == 200 and response.get('success', False):
            await state.set_state(SendOwnedArts.arts)

            total_arts = response["arts"]
            offset = 0

            await call.message.answer(
                f'Список работ, которыми вы обладаете(всего: {len(total_arts)})\nПоказать их по отдельности ?',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Продолжить",
                                              callback_data='continue_send_arts')],
                        [InlineKeyboardButton(text="Меню", callback_data='view_menu')]
                    ]
                ))
            await state.update_data(total_arts=total_arts, offset=offset)

    except Exception:
        await call.message.answer(f'Произошла ошибка, попробуйте купить работу позже',
                                  reply_markup=InlineKeyboardMarkup(
                                      inline_keyboard=[
                                          [InlineKeyboardButton(text="Меню", callback_data='view_menu')]
                                      ]
                                  ))


@view_arts_router.callback_query(F.data == 'continue_send_arts')
async def continue_send_arts(call: CallbackQuery, state: FSMContext):
    await call.bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    data = await state.get_data()
    offset = data.get('offset', 0)
    total_arts = data.get('total_arts', [])
    cur_arts = total_arts[offset:offset + 10]
    offset += len(cur_arts)

    await state.update_data(total_arts=total_arts, offset=offset)

    for art in cur_arts:
        await asyncio.sleep(0.5)
        await call.message.answer(f'Название: {art["name"]};\n'
                                  f'id: {art["id"]};\n'
                                  f'Краткое описание: {art["short_description"]}')
    if offset < len(total_arts):
        await state.update_data(total_arts=total_arts[min(len(total_arts), 10):])
        await call.message.answer('Продолжить показ работ ?',
                                  reply_markup=InlineKeyboardMarkup(
                                      inline_keyboard=[
                                          [InlineKeyboardButton(text="Продолжить",
                                                                callback_data='continue_send_arts')],
                                          [InlineKeyboardButton(text="Стоп", callback_data='view_menu')]
                                      ]
                                  ))
    else:
        await state.clear()
        await call.message.answer("Это все ваши работы",
                                  reply_markup=InlineKeyboardMarkup(
                                      inline_keyboard=[
                                          [InlineKeyboardButton(text="Меню", callback_data='view_menu')]
                                      ]))
