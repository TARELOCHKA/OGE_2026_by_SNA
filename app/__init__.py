from flask import Flask
from .config import Config
from .routes import bp
from dotenv import load_dotenv
import os

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(bp)

    # Проверка рабочей директории при запуске (для отладки)
    if app.config.get("DEBUG", False):
        print(f"[DEBUG] Working directory: {os.getcwd()}")
        print(f"[DEBUG] App root: {os.path.dirname(os.path.abspath(__file__))}")

    return app
