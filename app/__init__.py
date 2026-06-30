# ─────────────────────────────────────────────────────────────────
#  app/__init__.py
#  Veltrix – Application Factory
# ─────────────────────────────────────────────────────────────────

import tempfile
from datetime import datetime, timezone

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

from app.config import get_config

# ────────────────────────────────────────────────────────────────
# Extensions
# ────────────────────────────────────────────────────────────────
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    """
    Application Factory
    """

    # =============================================================
    # VERCEL FIX
    # Gunakan folder /tmp sebagai instance_path karena /var/task
    # bersifat read-only di Vercel.
    # =============================================================
    app = Flask(
        __name__,
        instance_path=tempfile.gettempdir()
    )

    # =============================================================
    # Load Config
    # =============================================================
    app.config.from_object(get_config())

    # =============================================================
    # Initialize Extensions
    # =============================================================
    db.init_app(app)
    migrate.init_app(app, db)

    # =============================================================
    # Flask Login
    # =============================================================
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # =============================================================
    # User Loader
    # =============================================================
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        demo_user = User()
        demo_user.id = 1
        demo_user.username = "Administrator"
        demo_user.email = "admin@vertix.com"
        demo_user.password = ""
        demo_user.created_at = datetime.now(timezone.utc)
        return demo_user

    # =============================================================
    # Jinja Global
    # =============================================================
    @app.context_processor
    def inject_globals():
        return {"now": lambda: datetime.now(timezone.utc)}

    # =============================================================
    # Register Blueprints
    # =============================================================
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # =============================================================
    # JANGAN menjalankan create_all() di Vercel
    # Database sebaiknya dibuat melalui migration
    # =============================================================
    # with app.app_context():
    #     db.create_all()

    return app