from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime
from WebSite.data.db_session import SqlAlchemyBase


class ArtView(SqlAlchemyBase):
    __tablename__ = 'art_views'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    art_id = Column(Integer, ForeignKey('arts.id'))
    timestamp = Column(DateTime, default=datetime.datetime.now)

    user = relationship('User', backref='viewed_arts')
    art = relationship('Arts', backref='view_art')
