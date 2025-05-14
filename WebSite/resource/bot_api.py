import logging
import os
from functools import wraps

from flask import request
from flask_restful import Resource
from email_validator import validate_email, EmailNotValidError
from sqlalchemy import func

from WebSite.data import db_session
from WebSite.data.art_views import ArtView
from WebSite.data.arts import Arts
from WebSite.data.category import Category
from WebSite.data.users import User
from WebSite.data.login_chat_bot import TelegramLogin
from config import API_TEXTS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def with_db(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        db_sess = db_session.create_session()
        try:
            rv = f(self, db_sess, *args, **kwargs)
            db_sess.commit()
            return rv
        except Exception:
            db_sess.rollback()
            raise
        finally:
            db_sess.close()

    return wrapper


def api_response_error(key):
    text = API_TEXTS.get(key)
    if not text:
        text = {"status": 500, 'error': 'Неизвестная ошибка.', "user_message": "🚧 Непредвиденная ошибка."}
    payload = {"success": False, 'error': text['error'], "user_message": text["user_message"]}
    return payload, text["status"]


def require_json(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if not request.is_json:
            return api_response_error("expected_json")
        return f(self, *args, **kwargs)

    return wrapper


def get_data():
    try:
        return request.get_json()
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        return None


class RegisterResource(Resource):
    @require_json
    @with_db
    def post(self, db_sess):
        data = get_data()

        nick_name = data.get('nick_name', '').strip()
        password = data.get('password', '')
        password_again = data.get('password_again', '')

        if not all([nick_name, password, password_again]):
            return api_response_error("missing_fields")
        if password != password_again:
            return api_response_error("password_mismatch")

        if db_sess.query(User).filter_by(nick_name=nick_name).first():
            return api_response_error("user_exists")

        user = User(nick_name=nick_name, balance=30)
        user.set_password(password)
        db_sess.add(user)

        return {"success": True}, 200


class LoginResource(Resource):
    @require_json
    @with_db
    def post(self, db_sess):
        data = get_data()
        nick_name = data.get('nick_name', '')
        password = data.get('password', '')
        chat_id = data.get('chat_id')

        if not all([nick_name, password]):
            return api_response_error("missing_fields")

        user = db_sess.query(User).filter_by(nick_name=nick_name).first()
        if not user or not user.check_password(password):
            return api_response_error("auth_failed")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if login:
            login.user_id = user.id
        else:
            db_sess.add(TelegramLogin(chat_id=chat_id, user_id=user.id))

        return {"success": True}, 200


class LogoutResource(Resource):
    @require_json
    @with_db
    def post(self, db_sess):
        data = get_data()
        chat_id = data.get('chat_id')
        if not chat_id:
            return api_response_error("no_chat_id")

        chat = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not chat:
            return api_response_error("user_not_found")
        chat.user_id = None

        return {"success": True}, 200


class CheckBotLoginResource(Resource):
    @require_json
    @with_db
    def post(self, db_sess):
        data = get_data()

        chat_id = data.get('chat_id')
        if not chat_id:
            return api_response_error("no_chat_id")

        chat = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not chat:
            chat = TelegramLogin(chat_id=chat_id, user_id=None)
            db_sess.add(chat)

        return {'success': bool(chat.user_id)}, 200


class ArtsResource(Resource):
    @require_json
    @with_db
    def post(self, db_sess, art_id=None):
        data = get_data()
        chat_id = data.get('chat_id')
        if not chat_id:
            return api_response_error("no_chat_id")

        if art_id is not None:
            art = db_sess.query(Arts).filter_by(id=art_id).first()
        else:
            art = db_sess.query(Arts).order_by(func.random()).first()

        if not art:
            return api_response_error("art_not_found")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()

        if login and login.user_id:
            already_viewed = db_sess.query(ArtView).filter_by(
                user_id=login.user_id,
                art_id=art.id
            ).first()
            if not already_viewed:
                art.views += 1
                db_sess.add(ArtView(user_id=login.user_id, art_id=art.id))

        owner_chat = db_sess.query(TelegramLogin).filter_by(user_id=art.owner).first()

        result = {
            'id': art.id,
            'name': art.name,
            'description': art.description,
            'short_description': art.short_description,
            'price': art.price,
            'creation_time': art.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            'views': art.views,
            'extension': art.extension,
            'creator': art.creator_user.nick_name,
            'owner': art.owner_user.nick_name,
            'owner_chat_id': owner_chat.chat_id
        }

        return {"success": True, "art": result}, 200


class UserInfoResource(Resource):
    @require_json
    @with_db
    def post(self, db_sess):
        data = get_data()
        chat_id = data.get('chat_id')
        if not chat_id:
            return api_response_error("no_chat_id")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return api_response_error('tech_error')

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return api_response_error('user_not_found')

        result = {
            'id': user.id,
            'nick_name': user.nick_name,
            'email': user.email,
            'description': user.description,
            'balance': user.balance,
            'creation_time': user.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        return {'success': True, 'user': result}, 200


class ChangePasswordResource(Resource):
    @require_json
    @with_db
    def put(self, db_sess):
        data = get_data()
        chat_id = data.get('chat_id')

        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        again_new_password = data.get('again_new_password', '')

        if not all([old_password, new_password, again_new_password]):
            return api_response_error('fields_missing')
        if not chat_id:
            return api_response_error("no_chat_id")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return api_response_error('tech_error')

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return api_response_error('user_not_found')

        if not user.check_password(old_password):
            return api_response_error("wrong_old_password")

        if new_password != again_new_password:
            return api_response_error('new_password_mismatch')

        user.set_password(new_password)

        return {'success': True}, 200


class ChangeNickNameResource(Resource):
    @require_json
    @with_db
    def put(self, db_sess):
        data = get_data()

        chat_id = data.get('chat_id')
        new_nick = data.get('new_nick', '').strip()

        if not new_nick:
            return api_response_error('missing_fields')

        if not chat_id:
            return api_response_error("no_chat_id")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return api_response_error('user_not_found')

        if db_sess.query(User).filter_by(nick_name=new_nick).first():
            return api_response_error('user_exists')

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return api_response_error('user_not_found')

        user.nick_name = new_nick
        return {"success": True}, 200


class ChangeEmailResource(Resource):
    @require_json
    @with_db
    def put(self, db_sess):
        data = get_data()

        chat_id = data.get('chat_id')
        new_email = data.get('new_email', '').strip()

        if not new_email:
            return api_response_error('fields_missing')
        if not chat_id:
            return api_response_error("no_chat_id")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return api_response_error('tech_error')

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return api_response_error('user_not_found')

        if db_sess.query(User).filter_by(email=new_email).first():
            return api_response_error('email_in_use')

        try:
            valid = validate_email(new_email)
            new_email = valid.ascii_email
        except EmailNotValidError:
            return api_response_error('invalid_email')

        user.email = new_email

        return {'success': True}, 200


class ChangeDescriptionResource(Resource):
    @require_json
    @with_db
    def put(self, db_sess):
        data = get_data()
        chat_id = data.get('chat_id')
        new_desc = data.get('new_description', '')

        if not chat_id:
            return api_response_error("no_chat_id")
        if len(new_desc) > 1000:
            return api_response_error("description_too_long")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return api_response_error("user_not_found")

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return api_response_error("user_not_found")

        user.description = new_desc

        return {"success": True}, 200


class AddArtResource(Resource):
    @require_json
    @with_db
    def post(self, db_sess):
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        short_desc = request.form.get('short_description', '').strip()
        categories = request.form.get('categories', '')
        price = request.form.get('price')
        chat_id = request.form.get('chat_id')
        file = request.files.get('image')

        if not file or not file.filename:
            return api_response_error("file_missing")
        if not title or not price:
            return api_response_error("missing_fields")
        if not price.isdigit() or int(price) < 0:
            return api_response_error("invalid_price")
        if len(short_desc) > 28:
            return api_response_error("short_desc_too_long")

        cat_names = [c.strip() for c in categories.split(',') if c.strip()]

        if not cat_names:
            return api_response_error("no_categories")

        cat_objs = []

        for c in cat_names:
            cat = db_sess.query(Category).filter_by(name=c).first()
            if not cat:
                cat = Category(name=c)
                db_sess.add(cat)
            cat_objs.append(cat)

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return api_response_error("user_not_found")

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return api_response_error("user_not_found")

        ext = os.path.splitext(file.filename)[1]
        art = Arts(
            name=title,
            description=description,
            short_description=short_desc,
            price=int(price),
            creator=user.id,
            owner=user.id,
            extension=ext,
            categories=cat_objs
        )
        db_sess.add(art)

        path = os.path.join('WebSite/static/img/arts', f"{art.id}{ext}")
        file.save(path)

        return {"success": True, "art_id": art.id}, 200


class ViewOwnedArts(Resource):
    @require_json
    @with_db
    def post(self, db_sess):
        data = get_data()
        chat_id = data.get('chat_id')
        if not chat_id:
            return api_response_error("no_chat_id")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return api_response_error("user_not_found")

        arts = db_sess.query(Arts).filter_by(owner=login.user_id).all()

        result = [{
            'id': art.id,
            'name': art.name,
            'description': art.description,
            'short_description': art.short_description,
            'price': art.price,
            'creation_time': art.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
            'views': art.views,
            'extension': art.extension,
            'creator': art.creator_user.nick_name,
            'owner': art.owner_user.nick_name,
        } for art in arts]

        return {"success": True, "arts": result}, 200


class PurchaseArt(Resource):
    @require_json
    @with_db
    def post(self, db_sess, art_id):
        data = get_data()
        chat_id = data.get('chat_id')
        if not chat_id:
            return api_response_error("no_chat_id")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return api_response_error("user_not_found")

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return api_response_error("user_not_found")

        art = db_sess.query(Arts).filter_by(id=art_id).first()
        if not art:
            return api_response_error("art_not_found")
        if user.id == art.owner:
            return api_response_error("already_owner")
        if art.price < 0:
            return api_response_error("art_not_for_sale")
        if user.balance < art.price:
            return api_response_error("insufficient_funds")

        user.balance -= art.price
        art.owner = user.id

        return {"success": True}, 200
