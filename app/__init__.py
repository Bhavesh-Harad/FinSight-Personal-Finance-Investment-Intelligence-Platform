from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
mail = Mail()
oauth = OAuth()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)
    
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    from app.auth.routes import auth
    from app.main.routes import main
    from app.expenses.routes import expenses
    from app.budgets.routes import budgets
    from app.incomes.routes import incomes
    from app.investments.routes import investments
    from app.goals.routes import goals

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(expenses)
    app.register_blueprint(budgets)
    app.register_blueprint(incomes)
    app.register_blueprint(investments)
    app.register_blueprint(goals)

    return app
