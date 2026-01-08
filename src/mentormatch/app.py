from flask import Flask
from mentormatch.config import Config
from mentormatch.routes import bp as routes_bp
from mentormatch.matcher import Matcher, PeopleInfo
from mentormatch.models import db


def start_app():
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        app.people = PeopleInfo(db.session)
        app.matcher = Matcher(app.people)
    app.register_blueprint(routes_bp)
    return app


flask_app = start_app()
