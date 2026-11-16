import os
from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, bcrypt


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Для доступа к этой странице необходимо войти."
    login_manager.login_message_category = "info"
    bcrypt.init_app(app)

    from . import models  # noqa: F401
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.resumes import resumes_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(resumes_bp)

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    return app
