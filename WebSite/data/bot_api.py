from flask import request, Blueprint, make_response, jsonify, send_file
from flask_login import login_user
from sqlalchemy import func

from PIL import Image
from io import BytesIO
import json
import base64

from . import db_session
from .arts import Arts
from .users import User

import random

blueprint = Blueprint(
    'bot_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/bot_api/register', methods=['POST'])
def register():
    if request.method == 'POST':
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
        login_user(user, remember=True)

        return jsonify({'success': 'OK'})


@blueprint.route('/bot_api/login', methods=['POST'])
def login():
    if request.method == 'POST':
        if not request.json:
            return make_response(jsonify({'error': 'Произошла ошибка! Попробуйте еще раз'}), 400)

        nick_name = request.json['nick_name']
        password = request.json['password']

        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.nick_name == nick_name).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return jsonify({'success': 'OK'})
        return make_response(jsonify({'error': 'Неправильный логин или пароль',
                                      'user': user}), 400)


@blueprint.route('/bot_api/arts/get_random_art', methods=['GET'])
def get_art():
    db_sess = db_session.create_session()
    max_id = db_sess.query(func.max(Arts.id)).scalar()
    art = db_sess.query(Arts).get(random.randint(1, max_id))

    return jsonify(
        {
            'art': art.to_dict(only=(
                'name', 'short_description', 'price', 'creator', 'owner', 'views', 'creation_time', 'id', 'extension')),
        }
    )


@blueprint.route('/bot_api/arts/<int:art_id>', methods=['GET'])
def get_art_with_id(art_id):
    db_sess = db_session.create_session()
    art = db_sess.query(Arts).get(art_id)

    return jsonify(
        {
            'art': art.to_dict(only=(
                'name', 'short_description', 'price', 'creator', 'owner', 'views', 'creation_time', 'id', 'extension')),
        }
    )
