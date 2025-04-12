import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

from WebSite.data.db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    nick_name = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String, index=True, unique=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    balance = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    creation_time = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    history = sqlalchemy.Column(sqlalchemy.String, default='')

    arts = orm.relationship("Arts", back_populates='user')

    def __repr__(self):
        return f'<User> {self.nick_name}, {self.email}\n{self.description}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
