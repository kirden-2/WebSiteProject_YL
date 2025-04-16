import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Arts(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'arts'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    owner = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    price = sqlalchemy.Column(sqlalchemy.Integer, default=-1)
    creation_time = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    views = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    creator_user = orm.relationship('Users', foreign_keys=[creator], backref="arts_created")
    owner_user = orm.relationship('Users', foreign_keys=[owner], backref="arts_owned")
    categories = orm.relationship("Category",
                                  secondary="association",
                                  backref="arts")

    def __repr__(self):
        return f'<Art> {self.name}, {self.owner}, {self.creator}\n{self.description}\n{self.price}\n{self.views}'
