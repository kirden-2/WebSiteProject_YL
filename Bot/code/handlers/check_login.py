from ..config import SITE_API

import requests


def check_user_login_now(chat_id):
    response = requests.get(f'{SITE_API}/login/check_bot_login', json={'chat_id': chat_id}).json()

    return response['login_now']

