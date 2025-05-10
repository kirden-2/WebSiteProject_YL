from ..db_session import SqlAlchemyBase
import sqlalchemy
from sqlalchemy import Column, Integer


class Login_chat(SqlAlchemyBase):
    __tablename__ = 'login_chat_bot'

    chat_id = Column(Integer, primary_key=True, nullable=False, index=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
