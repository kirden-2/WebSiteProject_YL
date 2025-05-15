from TelegramBot.utils import fetch_post


async def check_user_login_now(chat_id):
    response, status = await fetch_post('/login/check_bot_login',
                                        {'chat_id': chat_id}
                                        )
    return response.get('success')
