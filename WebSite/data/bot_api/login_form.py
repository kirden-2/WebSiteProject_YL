from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

from ..db_session import SqlAlchemyBase
import sqlalchemy
from sqlalchemy import orm, Column, Integer, String, Boolean


class Login_chat(SqlAlchemyBase):
    __tablename__ = 'login_chat_bot'

    chat_id = Column(Integer, primary_key=True, nullable=False, index=True)
    login_now = Column(Boolean)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
