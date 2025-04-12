from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField
from wtforms.fields.simple import SubmitField, BooleanField
from wtforms.validators import DataRequired


class CreateForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    description = StringField('Описание', validators=[DataRequired()])
    category = StringField('Категория')
    sale = IntegerField('Цена', validators=[DataRequired()])
    is_sale = BooleanField('Работа продаётся?')
    submit = SubmitField('Опубликовать')
