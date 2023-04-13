from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

class SearchForm(FlaskForm):
    search_text = StringField('Sök efter senior')
    submit = SubmitField('Sök')
