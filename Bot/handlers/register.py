from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from Bot.keyboards.inline_kbs import send_register_kb, send_cancel_kb, send_retry_reg_kb, \
    send_start_not_login_kb
from config import SITE_API

import requests

register_route = Router()


class Reg_form(StatesGroup):
    check_reg_state = State()
    check_tg_reg_state = State()


@register_route.callback_query(F.data == 'register')
async def register(call: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()  # получаем текущий статус
    if current_state is not None:  # если статус не установлен, то ничего не делаем
        await state.clear()

    await call.message.edit_text('Выберите подходящий для вас способ регистрации', reply_markup=send_register_kb())
    await call.answer()


@register_route.callback_query(F.data == 'default_reg')
async def default_register(call: CallbackQuery, state: FSMContext):
    await state.set_state(Reg_form.check_reg_state)
    await call.message.edit_text(
        'Введите через знак ";" по очереди:\n1.Желаемое имя пользователя;\n'
        '2.Пароль(учтите, он должен быть надежным!);\n3.Подтверждение пароля',
        reply_markup=send_cancel_kb())
    await call.answer()


@register_route.message(Reg_form.check_reg_state)
async def check_register(call: CallbackQuery):
    current_data = [value.strip() for value in call.text.split(';')]
    try:
        json = {'nick_name': current_data[0],
                'password': current_data[1],
                'password_again': current_data[2]}
        req = requests.post(f'{SITE_API}/register', json=json).json()
        if req['success']:
            await call.answer('Регистрация прошла успешно, теперь вам необходимо зайти в созданную вами учетную запись',
                              reply_markup=send_start_not_login_kb())
    except IndexError:
        await call.answer(f'Введенные данные не соответствуют формату. Повторите попытку',
                          reply_markup=send_retry_reg_kb())
    except KeyError:
        await call.answer(f'{req["error"]}. Повторите попытку', reply_markup=send_retry_reg_kb())
    except ConnectionError:
        await call.answer(
            f'Не удается установить подключение с нашим сайтом. Мы уже работаем над устранением проблемы.')
    except Exception:
        pass


@register_route.callback_query(F.data == 'telegram_reg')
async def tg_register(call: CallbackQuery, state: FSMContext):
    await state.set_state(Reg_form.check_tg_reg_state)
    await call.message.edit_text(
        "В качестве имени пользователя будет использован ваш username. "
        "Напишите через ; желаемый пароль в чат и его подтверждение")
    await call.answer()


@register_route.message(Reg_form.check_tg_reg_state)
async def check_tg_register(message: Message):
    current_data = [value.strip() for value in message.text.split(';')]
    try:
        json = {'nick_name': f'{message.from_user.first_name}_{message.from_user.last_name}',
                'password': current_data[0],
                'password_again': current_data[1]}
        req = requests.post(f'{SITE_API}/register', json=json).json()
        if req['success']:
            await message.answer('Регистрация прошла успешно', reply_markup=send_start_not_login_kb())
    except IndexError:
        await message.answer(f'Введенные данные не соответствуют формату. Повторите попытку',
                             reply_markup=send_retry_reg_kb())
    except KeyError:
        await message.answer(f'{req["error"]}', reply_markup=send_retry_reg_kb())
    except ConnectionError:
        await message.answer(
            f'Не удается установить подключение с нашим сайтом. Мы уже работаем над устранением проблемы.')
    except Exception:
        pass
