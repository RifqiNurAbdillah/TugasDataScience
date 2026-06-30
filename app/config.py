# ─────────────────────────────────────────────────────────────────
#  app/config.py
# ─────────────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-fallback-secret-key-change-in-production"
    )

    # ============================================================
    # DATABASE
    #
    # Jika DATABASE_URL ada -> gunakan PostgreSQL/MySQL
    # Jika tidak -> gunakan SQLite di /tmp (khusus Vercel)
    # ============================================================

    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/database.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)