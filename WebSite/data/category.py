from sqlalchemy import orm, Column, Integer, String

from WebSite.data.db_session import SqlAlchemyBase
from WebSite.data.association import association_table

class Category(SqlAlchemyBase):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)

    arts = orm.relationship('Arts',
                            secondary=association_table,
                            back_populates="categories")
