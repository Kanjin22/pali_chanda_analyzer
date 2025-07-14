# app/__init__.py
import os
from flask import Flask

def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pali-chanda-center-secret-key')
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance')
    os.makedirs(instance_path, exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_path, 'chanda_center.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Initialize Extensions ---
    from .extensions import db, migrate, login_manager
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "กรุณาล็อกอินเพื่อเข้าถึงหน้านี้"

    # Import models here, outside of app_context, for blueprint and user_loader access
    from . import models

    # --- User Loader ---
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # --- Register Blueprints ---
    from .main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from .admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from .analyzer.routes import analyzer as analyzer_blueprint
    app.register_blueprint(analyzer_blueprint, url_prefix='/analyzer')

    # --- Register CLI commands ---
    from . import cli
    cli.register_commands(app)

    return app