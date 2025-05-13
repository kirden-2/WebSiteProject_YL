import os

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


class RegisterResource(Resource):
    def post(self):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()

        nick_name = data.get('nick_name', '')
        password = data.get('password', '')
        password_again = data.get('password_again', '')

        if not all((nick_name, password_again, password)):
            return {'success': False, 'error': 'Имя или пароль не указаны',
                    'user_message': 'Укажите имя пользователя и пароль.'}, 400
        if password != password_again:
            return {'success': False, 'error': 'Пароли не совпадают',
                    'user_message': 'Пароли должны быть идентичными.'}, 400

        db_sess = db_session.create_session()

        if db_sess.query(User).filter_by(nick_name=nick_name).first():
            return {'success': False, 'error': 'Пользователь с таким именем уже существует',
                    'user_message': 'Такой пользователь уже зарегистрирован.'}, 400

        user = User(
            nick_name=nick_name
        )
        user.set_password(password)
        db_sess.add(user)
        db_sess.commit()

        return {'success': True}, 200


class LoginResource(Resource):
    def post(self):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()

        nick_name = data.get('nick_name', '')
        password = data.get('password', '')
        chat_id = data.get('chat_id', '')

        if not nick_name or not password:
            return {'success': False, 'error': 'Не все поля заполнены',
                    'user_message': 'Введите имя пользователя и пароль.'}, 400

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter_by(nick_name=nick_name).first()

        if not user or not user.check_password(password):
            return {'success': False, 'error': 'Не верный логин или пароль',
                    'user_message': 'Неверное имя пользователя или пароль.'}, 401

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if login:
            login.user_id = user.id
        else:
            login = TelegramLogin(chat_id=chat_id, user_id=user.id)
            db_sess.add(login)
        db_sess.commit()
        return {'success': True}, 200


class LogoutResource(Resource):
    def post(self):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()

        chat_id = data.get('chat_id', '')
        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        db_sess = db_session.create_session()

        chat = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not chat:
            return {'success': False, 'error': 'Пользователь не вошёл в систему',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 403
        chat.user_id = None
        db_sess.commit()
        return {'success': True}, 200


class CheckBotLoginResource(Resource):
    def post(self):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()

        chat_id = data.get('chat_id', '')
        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        db_sess = db_session.create_session()

        chat = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not chat:
            chat = TelegramLogin(chat_id=chat_id, user_id=None)
            db_sess.add(chat)
            db_sess.commit()

        return {'success': bool(chat.user_id)}, 200


class ArtsResource(Resource):
    def post(self, art_id=None):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()
        chat_id = data.get('chat_id', '')
        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        db_sess = db_session.create_session()

        if art_id is not None:
            art = db_sess.query(Arts).filter_by(id=art_id).first()
        else:
            art = db_sess.query(Arts).order_by(func.random()).first()

        if not art:
            return {'success': False, 'error': 'Не удалось найти работу',
                    'user_message': 'Не удалось найти работу. Попробуйте снова.'}, 404

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()

        if login and login.user_id:
            user_id = login.user_id

            already_viewed = db_sess.query(ArtView).filter_by(
                user_id=user_id,
                art_id=art.id
            ).first()
            if not already_viewed:
                art.views += 1
                db_sess.add(ArtView(user_id=user_id, art_id=art.id))
                db_sess.commit()

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

        return {'success': True, 'art': result}, 200


class UserInfoResource(Resource):
    def post(self):
        db_sess = db_session.create_session()

        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()
        chat_id = data.get('chat_id', '')

        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return {'success': False, 'error': 'Не удалось найти запись telegram-user',
                    'user_message': 'Техническая ошибка. Попробуйте перезайти в аккаунт или сделать запрос позже.'}, 404

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return {'success': False, 'error': 'Не удалось найти пользователя',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 404

        result = {
            'id': user.id,
            'nick_name': user.nick_name,
            'email': user.email,
            'description': user.description,
            'balance': user.balance,
            'creation_time': user.creation_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        return {'success': True,
                'user': result}, 200


class ChangePasswordResource(Resource):
    def put(self):
        db_sess = db_session.create_session()
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()

        chat_id = data.get('chat_id', '')
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        again_new_password = data.get('again_new_password', '')

        if not all([old_password, new_password, again_new_password]):
            return {'success': False, 'error': 'Отсутствуют обязательные поля',
                    'user_message': 'Не все поля заполнены. Повторите попытку снова.'}, 400
        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return {'success': False, 'error': 'Не найти запись telegram-user',
                    'user_message': 'Техническая ошибка. Попробуйте перезайти в аккаунт или сделать запрос позже.'}, 404

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return {'success': False, 'error': 'Не удалось найти пользователя',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 404

        if not user.check_password(old_password):
            return {'success': False, 'error': 'Неверный текущий пароль',
                    'user_message': 'Не верный пароль от аккаунта.'}, 403

        if new_password != again_new_password:
            return {'success': False, 'error': 'Пароли не совпадают', 'user_message': 'Пароли не совпадают.'}, 400

        user.set_password(new_password)
        db_sess.commit()
        return {'success': True}, 200


class ChangeEmailResource(Resource):
    def put(self):
        db_sess = db_session.create_session()
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()

        chat_id = data.get('chat_id', '')
        new_email = data.get('new_email', '')

        if not new_email:
            return {'success': False, 'error': 'В запросе отсутствует почта',
                    'user_message': 'Почта не указана. Попробуйте снова'}, 400
        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        login = db_sess.query(TelegramLogin).get(chat_id)
        if not login:
            return {'success': False, 'error': 'Не удалось найти запись telegram-user',
                    'user_message': 'Техническая ошибка. Попробуйте перезайти в аккаунт или сделать запрос позже.'}, 404

        user = db_sess.query(User).get(login.user_id)
        if not user:
            return {'success': False, 'error': 'Не удалось найти пользователя',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 404

        try:
            valid = validate_email(new_email)
            new_email = valid.ascii_email
        except EmailNotValidError:
            return {'success': False, 'error': 'Неверный формат почты',
                    'user_message': 'Неверный формат почты. Повторите попытку.'}, 400

        user.email = new_email
        db_sess.commit()

        return {'success': True}, 200


class ChangeDescriptionResource(Resource):
    def put(self):
        db_sess = db_session.create_session()
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()
        chat_id = data.get('chat_id', '')
        new_description = data.get('new_description', '')

        login = db_sess.query(TelegramLogin).get(chat_id)
        if not login:
            return {'success': False, 'error': 'Не удалось найти запись telegram-user',
                    'user_message': 'Техническая ошибка. Попробуйте перезайти в аккаунт или сделать запрос позже.'}, 404

        user = db_sess.query(User).get(login.user_id)
        if not user:
            return {'success': False, 'error': 'Не удалось найти пользователя',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 404

        if len(new_description) > 1000:
            return {'success': False, 'error': 'Кол-во символов в описании превысило лимит',
                    'user_message': 'Длина описания превысила лимит(1000 символов).'}, 400

        user.description = new_description
        db_sess.commit()

        return {'success': True}, 200


class AddArtResource(Resource):
    def post(self):
        db_sess = db_session.create_session()

        title = request.form.get("title", "")
        description = request.form.get("description", "")
        short_description = request.form.get("short_description", "")
        categories = request.form.get("categories", "")
        price = request.form.get("price", "")
        chat_id = request.form.get("chat_id", "")

        file = request.files.get("image")
        if not file or file.filename == '':
            return {'success': False, 'error': 'Файл не получен',
                    'user_message': 'Не удалось получить работу. Попробуйте снова.'}, 400

        if not title or not price:
            return {'success': False, 'error': 'Не все поля заполнены',
                    'user_message': 'Не все поля заполнены. Попробуйте снова.'}, 400

        if not price.isdigit() or int(price) < 0:
            return {'success': False, 'error': 'Цена не является целым положительным числом',
                    'user_message': 'Цена должна являться целым положительным числом. Попробуйте снова.'}, 400

        cat_names = set(c.strip() for c in categories.split(',') if c.strip())

        if not cat_names:
            return {'success': False, 'error': 'Категория не указана',
                    'user_message': 'У работы должны быть хотя бы одна категория. Попробуйте снова.'}, 400

        categories = []

        for c in cat_names:
            cat = db_sess.query(Category).filter_by(name=c).first()
            if not cat:
                cat = Category(name=c)
                db_sess.add(cat)
            categories.append(cat)

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return {'success': False, 'error': 'Не удалось найти запись telegram-user',
                    'user_message': 'Техническая ошибка. Попробуйте перезайти в аккаунт или сделать запрос позже.'}, 404

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return {'success': False, 'error': 'Не удалось найти запись user',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 404

        ext = os.path.splitext(file.filename)[1]
        art = Arts(
            name=title,
            description=description,
            short_description=short_description,
            price=int(price),
            creator=user.id,
            owner=user.id,
            extension=ext,
            categories=categories
        )
        db_sess.add(art)
        db_sess.commit()

        file_path = os.path.join('WebSite/static/img/arts', f'{art.id}{ext}')
        file.save(file_path)

        return {'success': 'OK', 'art_id': art.id}, 200


class ViewOwnedArts(Resource):
    def post(self):
        db_sess = db_session.create_session()

        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()

        chat_id = data.get('chat_id', '')
        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 404

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return {'success': False, 'error': 'Не удалось найти запись telegram-user',
                    'user_message': 'Техническая ошибка. Попробуйте перезайти в аккаунт или сделать запрос позже.'}, 404

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

        return {'success': True, 'arts': result}


class PurchaseArt(Resource):
    def post(self, art_id):
        db_sess = db_session.create_session()

        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 400

        data = request.get_json()

        chat_id = data.get('chat_id', '')
        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 404

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not login:
            return {'success': False, 'error': 'Не удалось найти запись telegram-user',
                    'user_message': 'Не удалось найти вас, попробуйте перезайти в аккаунт.'}, 404

        user = db_sess.query(User).filter_by(id=login.user_id).first()
        if not user:
            return {'success': False, 'error': 'Не удалось найти запись user',
                    'user_message': 'Техническая ошибка. Повторите попытку позже.'}, 404

        art = db_sess.query(Arts).filter_by(id=art_id).first()
        if not art:
            return {'success': False, 'error': 'Не удалось найти запись art',
                    'user_message': 'Не удалось найти работу.'}, 404

        if user.id == art.owner:
            return {'success': False, 'error': 'Пользователь уже является владельцем работы',
                    'user_message': 'Вы уже являетесь владельцем этой работы'}, 403

        if user.balance < art.price:
            return {'success': False, 'error': 'Нехватка средств для покупки',
                    'user_message': 'У вас не хватает средств для покупки этой работы.'}, 403

        if art.price < 0:
            return {'success': False, 'error': 'Работа не продаётся', 'user_message': 'Данная работа не продаётся'}, 403

        user.balance -= art.price
        art.owner = user.id
        db_sess.commit()

        return {'success': True}, 200
