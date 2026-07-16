from flask_wtf import FlaskForm
from wtforms import FloatField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from datetime import datetime

class BudgetForm(FlaskForm):
    category = SelectField('Category', choices=[
        ('Overall', 'Overall (All Categories)'),
        ('Food', 'Food'),
        ('Transport', 'Transport'),
        ('Housing', 'Housing'),
        ('Utilities', 'Utilities'),
        ('Healthcare', 'Healthcare'),
        ('Entertainment', 'Entertainment'),
        ('Education', 'Education'),
        ('Shopping', 'Shopping'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    month = IntegerField('Month (1-12)', validators=[DataRequired(), NumberRange(min=1, max=12)], default=datetime.today().month)
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=2000)], default=datetime.today().year)
    submit = SubmitField('Save Budget')
