from flask import request, make_response, jsonify
from flask_restful import Resource, abort
from pyexpat.errors import messages
from sqlalchemy import func

from WebSite.data import db_session
from WebSite.data.art_views import ArtView
from WebSite.data.arts import Arts
from WebSite.data.users import User
from WebSite.data.login_chat_bot import TelegramLogin

import random


class RegisterResource(Resource):
    def post(self):
        if not request.json:
            return jsonify({'error': 'Произошла ошибка! Приносим свои извинения, попробуйте еще раз'})

        nick_name = request.json['nick_name']
        password = request.json['password']
        password_again = request.json['password_again']

        error = None

        if not nick_name or not password:
            error = "Не все поля заполнены."
        if password != password_again:
            error = "Пароли не совпадают."
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.nick_name == nick_name).first():
            error = 'Такое име уже используется'

        if error:
            return jsonify({'error': error, })

        user = User(
            nick_name=nick_name
        )
        user.set_password(password)
        db_sess.add(user)
        db_sess.commit()

        return jsonify({'success': 'OK'})


class LoginResource(Resource):
    def post(self):
        if not request.json:
            return make_response(jsonify({'error': 'Произошла ошибка! Попробуйте еще раз'}), 400)

        nick_name = request.json['nick_name']
        password = request.json['password']
        chat_id = request.json['chat_id']

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.nick_name == nick_name).first()
        if user and user.check_password(password):
            try:
                chat = db_sess.query(TelegramLogin).filter(TelegramLogin.chat_id == chat_id).first()
                chat.login_now = True
                chat.user_id = user.id
                db_sess.commit()
            except Exception:
                chat = TelegramLogin(chat_id=chat_id, user_id=user.id)
                db_sess.add(chat)
                db_sess.commit()

            return jsonify({'success': 'OK'})

        return make_response(jsonify({'error': 'Неправильный логин или пароль'}), 400)


class LogoutResource(Resource):
    def post(self):
        if not request.json:
            return make_response(jsonify({'error': 'Произошла ошибка! Попробуйте еще раз'}), 400)

        chat_id = request.json['chat_id']

        db_sess = db_session.create_session()
        chat = db_sess.query(TelegramLogin).filter(TelegramLogin.chat_id == chat_id).first()
        chat.user_id = None
        db_sess.commit()
        return jsonify({'success': 'OK'})


class CheckBotLoginResource(Resource):
    def post(self):
        data = request.get_json(silent=True)
        if not data or 'chat_id' not in data:
            return make_response(
                jsonify({'error': 'Произошла ошибка! Отсутствует chat_id'}),
                400
            )

        chat_id = data['chat_id']
        db_sess = db_session.create_session()

        chat = db_sess.query(TelegramLogin).get(chat_id)
        if not chat:
            chat = TelegramLogin(chat_id=chat_id, user_id=None)
            db_sess.add(chat)
            db_sess.commit()

        return jsonify({'login_now': bool(chat.user_id)})


class RandomArtsResource(Resource):
    def post(self):
        db_sess = db_session.create_session()
        art = db_sess.query(Arts).order_by(func.random()).first()
        if not art:
            abort(404, message=f"Работа не найдена")

        chat_id = request.json.get('chat_id')
        if not chat_id:
            abort(404, message=f"Отсутствует chat_id")

        login = db_sess.query(TelegramLogin).get(chat_id)
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
                    'name', 'short_description', 'price', 'creator', 'owner', 'views', 'creation_time', 'id',
                    'extension')),
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

        login = db_sess.query(TelegramLogin).get(chat_id)
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
                    'name', 'short_description', 'price', 'creator', 'owner', 'views', 'creation_time', 'id',
                    'extension')),
            }
        )


class UserInfoResource(Resource):
    def get(self):
        db_sess = db_session.create_session()

        chat_id = request.json['chat_id']

        user = db_sess.query(User).get(db_sess.query(TelegramLogin).get(chat_id).user_id)

        return jsonify(
            {
                'user': user.to_dict(only=(
                    'id', 'nick_name', 'email', 'description', 'balance', 'creation_time'
                ))
            }
        )


class ChangePasswordResource(Resource):
    def put(self):
        db_sess = db_session.create_session()

        chat_id = request.json['chat_id']
        old_password = request.json['old_password']
        new_password = request.json['new_password']

        user = db_sess.query(User).get(db_sess.query(TelegramLogin).get(chat_id).user_id)

        if user.check_password(old_password):
            user.set_password(new_password)
            db_sess.commit()
            return jsonify({'success': 'OK'})
        else:
            return jsonify({'error': 'Старый пароль не совпадает с текущим'})


class ChangeEmailResource(Resource):
    def put(self):
        db_sess = db_session.create_session()

        chat_id = request.json['chat_id']
        new_email = request.json['new_email']

        user = db_sess.query(User).get(db_sess.query(TelegramLogin).get(chat_id).user_id)

        if '@' not in new_email:
            return jsonify({'error': 'Email не соответствует формату'})

        user.email = new_email
        db_sess.commit()

        return jsonify({'success': 'OK'})


class ChangeDescriptionResource(Resource):
    def put(self):
        db_sess = db_session.create_session()

        chat_id = request.json['chat_id']
        new_description = request.json['new_description']

        user = db_sess.query(User).get(db_sess.query(TelegramLogin).get(chat_id).user_id)

        user.description = new_description
        db_sess.commit()

        return jsonify({'success': 'OK'})

    def post(self):
        data = request.get_json(silent=True)
        if not data or 'chat_id' not in data:
            return make_response(
                jsonify({'error': 'Произошла ошибка! Отсутствует chat_id'}),
                400
            )

        chat_id = data['chat_id']
        db_sess = db_session.create_session()

        chat = db_sess.query(TelegramLogin).get(chat_id)
        if not chat:
            chat = TelegramLogin(chat_id=chat_id, login_now=False, user_id=None)
            db_sess.add(chat)
            db_sess.commit()

        return jsonify({'login_now': bool(chat.login_now)})


class AddArtResource(Resource):
    def post(self):
        title = request.json["title"]
        description = request.json["description"]
        short_description = request.json["short_description"]
        price = request.json["price"]
        chat_id = request.json["chat_id"]

        file = request.json["image"]

        db_sess = db_session.create_session()
        user_id = db_sess.query(TelegramLogin).get(chat_id).user_id

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

        arts = db_sess.query(Arts).filter(Arts.owner == (db_sess.query(TelegramLogin).get(chat_id).user_id)).all()

        db_sess.close()

        return jsonify({'arts': [item.to_dict(
            only=('name', 'short_description', 'price', 'creator.nick_name', 'owner.nick_name', 'views',
                  'creation_time', 'id', 'extension')) for item in arts]})


class PurchaseArt(Resource):
    def post(self, art_id):
        chat_id = request.json["chat_id"]
        db_sess = db_session.create_session()

        user = db_sess.query(User).get(db_sess.query(TelegramLogin).get(chat_id).user_id)
        art = db_sess.query(Arts).get(art_id)

        if user.id == art.owner:
            return jsonify({'error': 'Вы уже являетесь обладателем этой работы'})

        if user.balance < art.price:
            return jsonify({'error': 'На вашем счету недостаточно средств'})

        user.balance -= art.price
        art.owner = user.id
        db_sess.commit()

        return jsonify({'success': 'Работа была успешно приобретена'})
