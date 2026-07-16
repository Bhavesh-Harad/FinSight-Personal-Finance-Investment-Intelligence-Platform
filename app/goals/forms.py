from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class GoalForm(FlaskForm):
    name = StringField('Goal Name', validators=[DataRequired()])
    target_amount = FloatField('Target Amount', validators=[DataRequired(), NumberRange(min=1)])
    deadline = DateField('Target Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Short-term', 'Short-term (< 3 years)'),
        ('Medium-term', 'Medium-term (3-7 years)'),
        ('Long-term', 'Long-term (7+ years)')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Goal')

class DepositFundsForm(FlaskForm):
    amount = FloatField('Amount to Deposit', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Transfer from Savings')

class WithdrawFundsForm(FlaskForm):
    amount = FloatField('Amount to Withdraw', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Transfer back to Savings')
