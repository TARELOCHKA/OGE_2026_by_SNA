from flask import Flask
from .config import Config
from .routes import bp
from dotenv import load_dotenv
load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(bp)
    return app
