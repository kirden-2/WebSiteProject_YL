from flask import request, make_response, jsonify
from flask_restful import Resource, abort
from email_validator import validate_email, EmailNotValidError
from sqlalchemy import func

from WebSite.data import db_session
from WebSite.data.art_views import ArtView
from WebSite.data.arts import Arts
from WebSite.data.users import User
from WebSite.data.login_chat_bot import TelegramLogin


class RegisterResource(Resource):
    def post(self):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON'}, 400
        db_sess = db_session.create_session()

        data = request.get_json()

        nick_name = data.get('nick_name', '')
        password = data.get('password', '')
        password_again = data.get('password_again', '')

        error = None

        if not nick_name or not password:
            error = "Не все поля заполнены."
        if password != password_again:
            error = "Пароли не совпадают."
        if db_sess.query(User).filter_by(nick_name=nick_name).first():
            error = 'Такое име уже используется'

        if error:
            return {'success': False, 'error': error}, 400

        user = User(
            nick_name=nick_name
        )
        user.set_password(password)
        db_sess.add(user)
        db_sess.commit()

        return {'success': 'OK'}, 200


class LoginResource(Resource):
    def post(self):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON'}, 400
        db_sess = db_session.create_session()

        data = request.get_json()

        nick_name = data.get('nick_name', '')
        password = data.get('password', '')
        chat_id = data.get('chat_id', '')

        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id'}, 400

        user = db_sess.query(User).filter_by(nick_name=nick_name).first()

        if user and user.check_password(password):
            login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
            if login:
                login.user_id = user.id
            else:
                login = TelegramLogin(chat_id=chat_id, user_id=user.id)
                db_sess.add(login)
            db_sess.commit()
            return {'success': 'OK'}, 200
        return {'success': False, 'error': 'Неправильный логин или пароль'}, 400


class LogoutResource(Resource):
    def post(self):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON'}, 400
        db_sess = db_session.create_session()

        data = request.get_json()

        chat_id = data.get('chat_id', '')

        chat = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        chat.user_id = None
        db_sess.commit()
        return {'success': 'OK'}


class CheckBotLoginResource(Resource):
    def post(self):
        if not request.is_json:
            return {'success': False, 'error': 'Ожидался JSON'}, 400

        data = request.get_json()
        chat_id = data.get('chat_id', '')

        if not chat_id:
            return {'success': False, 'error': 'Не удалось найти chat_id'}, 400

        db_sess = db_session.create_session()

        chat = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        if not chat:
            chat = TelegramLogin(chat_id=chat_id, user_id=None)
            db_sess.add(chat)
            db_sess.commit()

        return {'success': bool(chat.user_id)}, 200


class RandomArtsResource(Resource):
    def post(self):
        db_sess = db_session.create_session()
        art = db_sess.query(Arts).order_by(func.random()).first()
        if not art:
            abort(404, message=f"Работа не найдена")

        chat_id = request.json.get('chat_id')
        if not chat_id:
            abort(404, message=f"Отсутствует chat_id")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        user_id = login.user_id if login else None

        if user_id:
            already_viewed = db_sess.query(ArtView).filter_by(
                user_id=user_id,
                art_id=art.id
            ).first()
            if not already_viewed:
                art.views += 1
                db_sess.add(ArtView(user_id=user_id, art_id=art.id))
                db_sess.commit()
        return jsonify(
            {
                'art': art.to_dict(only=(
                    'name', 'short_description', 'price', 'creator_user.nick_name', 'owner_user.nick_name', 'views',
                    'creation_time', 'id',
                    'extension'))
            }
        )


class ArtsResource(Resource):
    def post(self, art_id):
        db_sess = db_session.create_session()
        art = db_sess.query(Arts).get(art_id)
        if not art:
            abort(404, message=f"Работа с id:{art_id} не найдена")

        chat_id = request.json.get('chat_id')
        if not chat_id:
            abort(404, message=f"Отсутствует chat_id")

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        user_id = login.user_id if login else None

        if user_id:
            already_viewed = db_sess.query(ArtView).filter_by(
                user_id=user_id,
                art_id=art_id
            ).first()
            if not already_viewed:
                art.views += 1
                db_sess.add(ArtView(user_id=user_id, art_id=art_id))
                db_sess.commit()

        return jsonify(
            {
                'art': art.to_dict(only=(
                    'name', 'short_description', 'price', 'creator_user.nick_name', 'owner_user.nick_name', 'views',
                    'creation_time', 'id',
                    'extension'))
            }
        )


class UserInfoResource(Resource):
    def post(self):
        db_sess = db_session.create_session()
        try:
            if not request.is_json:
                return {'success': False, 'error': 'Ожидался JSON'}, 400

            data = request.get_json()
            chat_id = data.get('chat_id', '')

            if not chat_id:
                return {'success': False, 'error': 'Не удалось найти chat_id'}, 400

            login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
            if not login:
                return {'success': False, 'error': 'Не найти запись telegram-user'}, 404

            user = db_sess.query(User).filter_by(id=login.user_id).first()
            if not user:
                return {'success': False, 'error': 'Не найти пользователя'}, 404

            return {'success': True,
                    'user': user.to_dict(
                        only=('id', 'nick_name', 'email', 'description', 'balance', 'creation_time'))}, 200
        except Exception:
            return {'success': False, 'error': f'Внутренняя ошибка сервера'}, 500


class ChangePasswordResource(Resource):
    def put(self):
        db_sess = db_session.create_session()
        try:
            if not request.is_json:
                return {'success': False, 'error': 'Ожидался JSON'}, 400

            data = request.get_json()

            chat_id = data.get('chat_id', '')
            old_password = data.get('old_password', '')
            new_password = data.get('new_password', '')
            again_new_password = data.get('again_new_password', '')

            if not all([old_password, new_password, again_new_password]):
                return {'success': False, 'error': 'Отсутствуют обязательные поля'}, 400
            if not chat_id:
                return {'success': False, 'error': 'Не удалось найти chat_id'}, 400

            login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
            if not login:
                return {'success': False, 'error': 'Не найти запись telegram-user'}, 404

            user = db_sess.query(User).filter_by(id=login.user_id).first()
            if not user:
                return {'success': False, 'error': 'Не найти пользователя'}, 404

            if not user.check_password(old_password):
                return {'success': False, 'error': 'Неверный текущий пароль'}, 403

            if new_password != again_new_password:
                return {'success': False, 'error': 'Пароли не совпадают'}, 400

            user.set_password(new_password)
            db_sess.commit()
            return {'success': True}, 200
        except Exception:
            return {'success': False, 'error': f'Внутренняя ошибка сервера'}, 500


class ChangeEmailResource(Resource):
    def put(self):
        db_sess = db_session.create_session()
        try:
            if not request.is_json:
                return {'success': False, 'error': 'Ожидался JSON'}, 400

            data = request.get_json()

            chat_id = data.get('chat_id', '')
            new_email = data.get('new_email', '')

            if not new_email:
                return {'success': False, 'error': 'В запросе отсутствует почта'}, 400
            if not chat_id:
                return {'success': False, 'error': 'Не удалось найти chat_id'}, 400

            login = db_sess.query(TelegramLogin).get(chat_id)
            if not login:
                return {'success': False, 'error': 'Не найти запись telegram-user'}, 404

            user = db_sess.query(User).get(login.user_id)
            if not user:
                return {'success': False, 'error': 'Не найти пользователя'}, 404

            try:
                valid = validate_email(new_email)
                new_email = valid.ascii_email
            except EmailNotValidError:
                return {'success': False, 'error': f'Неверный формат почты'}, 400

            user.email = new_email
            db_sess.commit()

            return {'success': True}, 200
        except Exception:
            return {'success': False, 'error': f'Внутренняя ошибка сервера'}, 500


class ChangeDescriptionResource(Resource):
    def put(self):
        db_sess = db_session.create_session()
        try:
            if not request.is_json:
                return {'success': False, 'error': 'Ожидался JSON'}, 400

            data = request.get_json()
            chat_id = data.get('chat_id', '')
            new_description = request.json['new_description']

            login = db_sess.query(TelegramLogin).get(chat_id)
            if not login:
                return {'success': False, 'error': 'Не найти запись telegram-user'}, 404

            user = db_sess.query(User).get(login.user_id)
            if not user:
                return {'success': False, 'error': 'Не найти пользователя'}, 404

            if len(new_description) > 1000:
                return {'success': False, 'error': 'Кол-во символов в описании превысило лимит'}, 400

            user.description = new_description
            db_sess.commit()

            return {'success': True}, 200
        except Exception:
            return {'success': False, 'error': f'Внутренняя ошибка сервера'}, 500


class AddArtResource(Resource):
    def post(self):
        title = request.json["title"]
        description = request.json["description"]
        short_description = request.json["short_description"]
        price = request.json["price"]
        chat_id = request.json["chat_id"]

        file = request.json["image"]

        db_sess = db_session.create_session()

        login = db_sess.query(TelegramLogin).get(chat_id)
        user_id = login.user_id

        art = Arts(
            name=title,
            description=description,
            short_description=short_description,
            price=int(price),
            creator=user_id,
            owner=user_id,
            extension='.jpg'
        )

        db_sess.add(art)
        db_sess.commit()

        art_id = db_sess.query(Arts).filter(Arts.name == title, Arts.price == price,
                                            Arts.description == description).first().id

        return jsonify({'success': 'OK', 'art_id': art_id})


class ViewOwnedArts(Resource):
    def get(self):
        chat_id = request.json["chat_id"]
        db_sess = db_session.create_session()

        login = db_sess.query(TelegramLogin).get(chat_id)

        arts = db_sess.query(Arts).filter(Arts.owner == login.user_id).all()

        db_sess.close()

        return jsonify({'arts': [item.to_dict(
            only=('name', 'short_description', 'price', 'creator.nick_name', 'owner.nick_name', 'views',
                  'creation_time', 'id', 'extension')) for item in arts]})


class PurchaseArt(Resource):
    def post(self, art_id):
        chat_id = request.json["chat_id"]
        db_sess = db_session.create_session()

        login = db_sess.query(TelegramLogin).filter_by(chat_id=chat_id).first()
        user = db_sess.query(User).filter_by(id=login.user_id).first()
        art = db_sess.query(Arts).filter_by(id=art_id).first()

        if user.id == art.owner:
            return jsonify({'error': 'Вы уже являетесь обладателем этой работы'})

        if user.balance < art.price:
            return jsonify({'error': 'На вашем счету недостаточно средств'})

        user.balance -= art.price
        art.owner = user.id
        db_sess.commit()

        return jsonify({'success': 'Работа была успешно приобретена'})
