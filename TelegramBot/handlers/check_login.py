from config import SITE_API
import requests


def check_user_login_now(chat_id):
    try:
        response = requests.post(f"{SITE_API}/login/check_bot_login",
                                 json={'chat_id': chat_id},
                                 timeout=5).json()
    except requests.RequestException:
        return False

    return response.get('success', False)
