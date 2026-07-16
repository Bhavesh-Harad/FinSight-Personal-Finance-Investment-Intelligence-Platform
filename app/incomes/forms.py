from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, NumberRange

class IncomeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    amount = FloatField('Amount (₹)', validators=[DataRequired(), NumberRange(min=0.01)])
    source = SelectField('Income Source', choices=[
        ('Salary', 'Salary'),
        ('Freelance', 'Freelance'),
        ('Investments', 'Investments'),
        ('Business', 'Business'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    description = TextAreaField('Description (Optional)')
    submit = SubmitField('Save Income')
