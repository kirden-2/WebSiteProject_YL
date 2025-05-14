import asyncio
import mimetypes

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import TelegramBot.bot
from TelegramBot.keyboards.inline_kbs import send_view_art_kb, send_art_kb
from TelegramBot.handlers.check_login import check_user_login_now

from aiogram.utils.chat_action import ChatActionSender

from TelegramBot.utils import fetch_post
from config import ALLOWED_EXTENSIONS, BOT_TEXTS

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
    try:
        response, status = await fetch_post(endpoint, {"chat_id": chat_id})
    except Exception:
        return {}, 500
    return response, status


async def add_art(message, state, bot):
    data = await state.get_data()

    file_id = data["image"].file_id
    file_info = await bot.get_file(file_id)
    file_bytes = await bot.download_file(file_info.file_path)

    filename = file_info.file_path.rsplit('/', 1)[-1]

    if not filename.lower().endswith(tuple(ALLOWED_EXTENSIONS)):
        await message.answer(
            BOT_TEXTS["unsupported_format"],
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=BOT_TEXTS["show_more"], callback_data='create_art')]
                ]
            ))
        return

    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        if filename.lower().endswith('.gif'):
            mime_type = 'image/gif'

    try:
        response, status = await fetch_post('/arts/add_artwork',
                                            {'title': data.get('title', ''),
                                             'description': data.get('description', ''),
                                             'short_description': data.get('short_description', ''),
                                             'price': data.get('price', ''),
                                             'categories': data.get('categories', ''),
                                             'chat_id': message.chat.id},
                                            file_bytes=file_bytes.getvalue(),
                                            field_name='image',
                                            filename=filename,
                                            content_type=mime_type
                                            )
    except Exception:
        await message.answer(
            BOT_TEXTS["network_error"],
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=BOT_TEXTS['menu_button'], callback_data='view_menu')]
                ]
            ))
        await state.clear()
        return

    if status == 200 and response.get('success'):
        await message.answer(
            BOT_TEXTS["saved_success"].format(art_id=response.get('art_id', 'n/a')),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=BOT_TEXTS['menu_button'], callback_data='view_menu')]
                ]
            ))
    else:
        rm = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BOT_TEXTS['menu_button'], callback_data='view_menu')] if status == 500
            else [InlineKeyboardButton(text=BOT_TEXTS['reload'], callback_data='create_art')]
        ])

        await message.answer(response.get('user_message', BOT_TEXTS["generic_error"]), reply_markup=rm)
    await state.clear()


@view_arts_router.callback_query(F.data == 'view_menu')
async def view_menu(call: CallbackQuery):
    await call.answer()
    text = BOT_TEXTS["menu_welcome"]
    markup = send_view_art_kb(login=check_user_login_now(call.message.chat.id))
    try:
        await call.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest:
        await call.message.answer(text, reply_markup=markup)


@view_arts_router.callback_query(F.data == 'view_random_art')
async def view_random_art(call: CallbackQuery):
    await call.answer()
    msg = await call.message.answer(BOT_TEXTS["search_random"])
    bot = call.bot
    response, status = await get_art(call.message.chat.id, '/arts')

    if status == 200 and response.get('success', False):
        try:
            async with ChatActionSender.upload_photo(bot=bot, chat_id=call.message.chat.id):
                art = response.get('art', {})
                caption = build_caption(art)
                path = f'WebSite/static/img/arts/{art["id"]}{art["extension"]}'
                file = FSInputFile(path)
                kb = send_art_kb(art.get('id', None), bool(art.get('owner_chat_id', '') == call.message.chat.id), True)

                if art["extension"].lower() == '.gif':
                    await call.message.answer_animation(animation=file, caption=caption, reply_markup=kb)
                else:
                    await call.message.answer_photo(photo=file, caption=caption, reply_markup=kb)

        except TelegramBadRequest as e:
            await call.message.answer(
                BOT_TEXTS["image_too_big"] if 'too big' in (e.message or '').lower() else BOT_TEXTS["load_error"],
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=BOT_TEXTS['reload'],
                                          callback_data='view_random_art')]
                ]))

    else:
        rm = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BOT_TEXTS['menu_button'], callback_data='view_menu')] if status == 500
            else [InlineKeyboardButton(text=BOT_TEXTS['reload'], callback_data='view_random_art')]
        ])

        await call.message.answer(response.get('user_message', BOT_TEXTS["generic_error"]), reply_markup=rm)
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)


@view_arts_router.callback_query(F.data == 'view_art_with_id')
async def get_art_id(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer(BOT_TEXTS["enter_id"])
    await state.set_state(ViewArt.get_id)


@view_arts_router.message(ViewArt.get_id)
async def view_art_with_id(message: Message):
    msg = await message.answer(BOT_TEXTS["searching_id"].format(id=message.text))
    bot = message.bot
    response, status = await get_art(message.chat.id, f'/arts/{message.text}')

    if status == 200 and response.get('success', False):
        try:
            async with ChatActionSender.upload_photo(bot=bot, chat_id=message.chat.id):
                art = response.get('art', {})
                caption = build_caption(art)
                path = f'WebSite/static/img/arts/{art["id"]}{art["extension"]}'
                file = FSInputFile(path)
                kb = send_art_kb(art["id"], art.get('owner_chat_id') == message.chat.id, False)

                if art["extension"].lower() == '.gif':
                    await message.answer_animation(animation=file, caption=caption, reply_markup=kb)
                else:
                    await message.answer_photo(photo=file, caption=caption, reply_markup=kb)

        except TelegramBadRequest as e:
            await message.answer(
                BOT_TEXTS["image_too_big"] if 'too big' in (e.message or '').lower() else BOT_TEXTS["load_error"],
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=BOT_TEXTS['reload'], callback_data='view_art_with_id')]
                    ]))

    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BOT_TEXTS['menu_button'], callback_data='view_menu')] if status == 500
            else [InlineKeyboardButton(text=BOT_TEXTS['reload'], callback_data='view_art_with_id')]
        ])

        await message.answer(response.get('user_message', BOT_TEXTS["generic_error"]), reply_markup=kb)
    await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)


@view_arts_router.callback_query(lambda c: c.data.startswith('purchase_artwork'))
async def check_purchase(call: CallbackQuery):
    await call.answer()
    art_id = call.data.split('_')[-1]
    await call.message.answer(BOT_TEXTS["confirm_purchase"].format(art_id=art_id),
                              reply_markup=InlineKeyboardMarkup(
                                  inline_keyboard=[
                                      [InlineKeyboardButton(text="✅ Подтверждаю",
                                                            callback_data=f'continue_purchase_{art_id}')],
                                      [InlineKeyboardButton(text="❌ Отмена", callback_data=f'view_menu')]
                                  ]
                              ))


@view_arts_router.callback_query(lambda c: c.data.startswith('continue_purchase_'))
async def purchase(call: CallbackQuery):
    await call.answer()
    art_id = call.data.split('_')[-1]
    response, status = await get_art(call.message.chat.id, f'/purchase/{art_id}')

    try:
        if not check_user_login_now(call.message.chat.id):
            raise PermissionError
        if status == 200 and response.get('success'):
            await call.message.answer(BOT_TEXTS["purchase_success"].format(art_id=art_id))
        else:
            raise Exception
    except PermissionError:
        await call.message.answer(BOT_TEXTS["not_logged_in"],
                                  reply_markup=InlineKeyboardMarkup(
                                      inline_keyboard=[
                                          [InlineKeyboardButton(text=BOT_TEXTS['logged_in'], callback_data='login')]
                                      ]
                                  ))
    except Exception:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BOT_TEXTS['menu_button'], callback_data='view_menu')] if status == 500
            else [InlineKeyboardButton(text=BOT_TEXTS['reload'], callback_data=call.data)]
        ])

        await call.message.answer(response.get('user_message', BOT_TEXTS["generic_error"]), reply_markup=kb)


@view_arts_router.callback_query(F.data == 'create_art')
async def create_art(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer(
        BOT_TEXTS["create_prompt"],
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='❌ Отмена', callback_data='view_menu')]
            ]
        )
    )
    await state.set_state(ArtData.image)


@view_arts_router.message(lambda message: message.photo)
async def set_image(message: Message, state: FSMContext):
    await state.update_data(image=message.photo[-1])
    await message.answer(BOT_TEXTS["ask_title"])
    await state.set_state(ArtData.title)


@view_arts_router.message(ArtData.title)
async def set_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(BOT_TEXTS["ask_description"])
    await state.set_state(ArtData.description)


@view_arts_router.message(ArtData.description)
async def set_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text if message.text.lower() != 'нет' else '')
    await message.answer(BOT_TEXTS["ask_short_desc"])
    await state.set_state(ArtData.short_description)


@view_arts_router.message(ArtData.short_description)
async def set_short_description(message: Message, state: FSMContext):
    await state.update_data(short_description=message.text if message.text.lower() != 'нет' else '')
    await message.answer(BOT_TEXTS["ask_category"])
    await state.set_state(ArtData.category)


@view_arts_router.message(ArtData.category)
async def set_category(message: Message, state: FSMContext):
    await state.update_data(categories=message.text)
    await message.answer(BOT_TEXTS["ask_price"])
    await state.set_state(ArtData.price)


@view_arts_router.message(ArtData.price)
async def set_price(message: Message, state: FSMContext, bot: TelegramBot):
    try:
        price = int(message.text)
    except ValueError:
        return await message.answer(BOT_TEXTS["invalid_price"])
    await state.update_data(price=price)
    await add_art(message, state, bot)


@view_arts_router.callback_query(F.data == 'owned_arts')
async def view_owned_arts(call: CallbackQuery, state: FSMContext):
    await call.answer()
    response, status = await get_art(call.message.chat.id, '/owned_arts')

    if status == 200 and response.get('success'):
        await state.set_state(SendOwnedArts.arts)

        total_arts = response["arts"]

        await call.message.answer(BOT_TEXTS["owned_intro"].format(n=len(total_arts)),
                                  reply_markup=InlineKeyboardMarkup(
                                      inline_keyboard=[
                                          [InlineKeyboardButton(text="▶️ Продолжить",
                                                                callback_data='continue_send_arts')],
                                          [InlineKeyboardButton(text="⏹️ Отмена", callback_data='view_menu')]
                                      ]
                                  ))
        await state.update_data(total_arts=total_arts, offset=0)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BOT_TEXTS['menu_button'], callback_data='view_menu')] if status == 500
            else [InlineKeyboardButton(text=BOT_TEXTS['reload'], callback_data='owned_arts')]
        ])

        await call.message.answer(
            response.get('user_message', BOT_TEXTS["generic_error"]),
            reply_markup=kb)


@view_arts_router.callback_query(F.data == 'continue_send_arts')
async def continue_send_arts(call: CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        await call.bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        data = await state.get_data()
        offset = data.get('offset', 0)
        total_arts = data.get('total_arts', [])
        cur_arts = total_arts[offset:offset + 10]

        for art in cur_arts:
            await asyncio.sleep(0.3)
            await call.message.answer(
                f'{art["name"]} - #{art["id"]};\n{art["short_description"] + '.' if art["short_description"] else ''}')

        offset += len(cur_arts)
        await state.update_data(offset=offset)

        if offset < len(total_arts):
            await state.update_data(total_arts=total_arts[min(len(total_arts), 10):])
            await call.message.answer('▶️ Продолжить показ работ ?',
                                      reply_markup=InlineKeyboardMarkup(
                                          inline_keyboard=[
                                              [InlineKeyboardButton(text=BOT_TEXTS['show_more'],
                                                                    callback_data='continue_send_arts')],
                                              [InlineKeyboardButton(text=BOT_TEXTS['stop'], callback_data='view_menu')]
                                          ]
                                      ))
        else:
            await state.clear()
            await call.message.answer(BOT_TEXTS["owned_end"],
                                      reply_markup=InlineKeyboardMarkup(
                                          inline_keyboard=[
                                              [InlineKeyboardButton(text=BOT_TEXTS['menu_button'],
                                                                    callback_data='view_menu')]
                                          ]))
    except Exception:
        await call.message.answer(BOT_TEXTS['technical_error'],
                                  reply_markup=InlineKeyboardMarkup(
                                      inline_keyboard=[
                                          [InlineKeyboardButton(text=BOT_TEXTS['menu_button'],
                                                                callback_data='view_menu')],
                                          [InlineKeyboardButton(text=BOT_TEXTS['reload'],
                                                                callback_data='owned_arts')]
                                      ]
                                  ))
