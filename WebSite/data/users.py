import datetime
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase
from sqlalchemy import orm, Column, DateTime, Integer, String
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nick_name = Column(String, nullable=False)
    email = Column(String, index=True, unique=True)
    hashed_password = Column(String, nullable=False)
    description = Column(String, nullable=True)
    balance = Column(Integer, default=0)
    creation_time = Column(DateTime, default=datetime.datetime.now)

    arts_created = orm.relationship("Arts", foreign_keys='Arts.creator', back_populates='creator_user')
    arts_owned = orm.relationship("Arts", foreign_keys='Arts.owner', back_populates='owner_user')

    def __repr__(self):
        return f'<User> {self.surname} {self.name} {self.age} {self.position}' \
               f' {self.speciality} {self.address} {self.email} {self.hashed_password}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
