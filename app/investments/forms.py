from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

class InvestmentForm(FlaskForm):
    name = StringField('Investment Name', validators=[DataRequired()])
    symbol = StringField('Ticker/Symbol (Optional)')
    asset_class = SelectField('Asset Class', choices=[
        ('Stock', 'Stock'),
        ('Mutual Fund', 'Mutual Fund'),
        ('ETF', 'ETF'),
        ('Bond', 'Bond'),
        ('Real Estate', 'Real Estate'),
        ('Crypto', 'Crypto'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    purchase_date = DateField('Purchase Date', format='%Y-%m-%d', validators=[DataRequired()])
    purchase_price = FloatField('Purchase Price (per unit)', validators=[DataRequired(), NumberRange(min=0.01)])
    quantity = FloatField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    current_price = FloatField('Current Price (Optional if Symbol provided)', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Save Investment')
