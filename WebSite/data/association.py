import sqlalchemy
from .db_session import SqlAlchemyBase

association_table = sqlalchemy.Table(
    'association',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('art_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('arts.id')),
    sqlalchemy.Column('category_id', sqlalchemy.Integer, sqlalchemy.ForeignKey('category.id'))
)