from datetime import datetime
from flask_login import UserMixin
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True, default='https://ui-avatars.com/api/?name=User&background=random')
    role = db.Column(db.String(20), nullable=False, default='User')
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    income_sources = db.Column(db.Text, nullable=True)
    financial_preferences = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    expenses = db.relationship('Expense', backref='author', lazy=True, cascade="all, delete-orphan")
    incomes = db.relationship('Income', backref='author', lazy=True, cascade="all, delete-orphan")
    budgets = db.relationship('Budget', backref='author', lazy=True, cascade="all, delete-orphan")
    investments = db.relationship('Investment', backref='author', lazy=True, cascade="all, delete-orphan")
    goals = db.relationship('Goal', backref='author', lazy=True, cascade="all, delete-orphan")

    def get_available_savings(self):
        total_income = sum(i.amount for i in self.incomes)
        total_expense = sum(e.amount for e in self.expenses)
        return total_income - total_expense

    def get_token(self, expires_sec=1800):
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_token(token, max_age=1800):
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=max_age)['user_id']
        except (SignatureExpired, BadSignature, KeyError):
            return None
        return User.query.get(user_id)

    @staticmethod
    def get_registration_token(user_data):
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(user_data)

    @staticmethod
    def verify_registration_token(token, max_age=1800):
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_data = s.loads(token, max_age=max_age)
        except (SignatureExpired, BadSignature):
            return None
        return user_data

    def __repr__(self):
        return f"User('{self.full_name}', '{self.email}')"

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    payment_mode = db.Column(db.String(50), nullable=False, default='Cash')
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Expense('{self.title}', '{self.amount}', '{self.category}', '{self.payment_mode}')"

class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Income('{self.title}', '{self.amount}', '{self.source}')"

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Budget('{self.category}', '{self.amount}', '{self.month}/{self.year}')"

class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    symbol = db.Column(db.String(20), nullable=True) # e.g., AAPL, VOO
    asset_class = db.Column(db.String(50), nullable=False) # e.g., Stock, ETF, Mutual Fund, Bond, Real Estate, Crypto, Other
    purchase_date = db.Column(db.Date, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False) # Price per unit
    quantity = db.Column(db.Float, nullable=False) # Number of units
    current_price = db.Column(db.Float, nullable=False) # Current price per unit
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def total_invested(self):
        return self.purchase_price * self.quantity

    def current_value(self):
        return self.current_price * self.quantity

    def absolute_return(self):
        return self.current_value() - self.total_invested()
        
    def percentage_return(self):
        if self.total_invested() == 0:
            return 0
        return (self.absolute_return() / self.total_invested()) * 100

    def __repr__(self):
        return f"Investment('{self.name}', '{self.asset_class}', '{self.quantity}')"

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, nullable=False, default=0.0)
    deadline = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False) # e.g., Short-term, Long-term
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def progress_percentage(self):
        if self.target_amount == 0:
            return 0
        return min((self.current_amount / self.target_amount) * 100, 100)
        
    def remaining_amount(self):
        return max(self.target_amount - self.current_amount, 0)
        
    def months_remaining(self):
        today = datetime.now().date()
        if self.deadline <= today:
            return 0
        
        diff_years = self.deadline.year - today.year
        diff_months = self.deadline.month - today.month
        total_months = diff_years * 12 + diff_months
        
        return max(total_months, 1) # At least 1 month if in the future

    def required_monthly_saving(self):
        months = self.months_remaining()
        if months == 0:
            return self.remaining_amount()
        return self.remaining_amount() / months

    def __repr__(self):
        return f"Goal('{self.name}', '{self.target_amount}', '{self.deadline}')"

