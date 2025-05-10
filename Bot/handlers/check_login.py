from config import SITE_API
import requests

def check_user_login_now(chat_id):
    url = f"{SITE_API}/login/check_bot_login"
    try:
        resp = requests.post(url, json={'chat_id': chat_id}, timeout=5)
    except requests.RequestException as e:
        print(f"Ошибка подключения к API ({url}): {e}")
        return False

    if resp.status_code != 200:
        print(f"API вернул {resp.status_code} на {url}: {resp.text}")
        return False

    try:
        data = resp.json()
    except ValueError:
        print(f"Некорректный JSON от {url}: {resp.text}")
        return False

    return bool(data.get('login_now', False))