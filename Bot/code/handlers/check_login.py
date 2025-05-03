import requests


def check_user_login_now(chat_id):
    response = requests.get('http://127.0.0.1:5000/bot_api/login/check_bot_login', json={'chat_id': chat_id}).json()

    return response['login_now']

