# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

class MyAnonymousUser(AnonymousUserMixin):
    def is_administrator(self):
        return False

login_manager.anonymous_user = MyAnonymousUser