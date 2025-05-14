from sqlalchemy import orm, Column, Integer, String, DateTime, ForeignKey
import datetime
from sqlalchemy_serializer import SerializerMixin

from WebSite.data.db_session import SqlAlchemyBase
from WebSite.data.association import association_table

class Arts(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'arts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    creator = Column(Integer, ForeignKey('users.id'))
    owner = Column(Integer, ForeignKey('users.id'))
    description = Column(String, nullable=True)
    short_description = Column(String, nullable=True)
    price = Column(Integer, default=-1)
    creation_time = Column(DateTime, default=datetime.datetime.now)
    views = Column(Integer, default=0)
    extension = Column(String)

    creator_user = orm.relationship('User', foreign_keys=[creator], back_populates="arts_created")
    owner_user = orm.relationship('User', foreign_keys=[owner], back_populates="arts_owned")
    categories = orm.relationship('Category',
                                  secondary=association_table,
                                  back_populates="arts")

    def __repr__(self):
        return f"<Art {self.name} id={self.id}, (creator={self.creator}, owner={self.owner})\nviews={self.views}, price={self.price}>"
