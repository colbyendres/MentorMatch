import logging
from authlib.integrations.flask_client import OAuth, OAuthError

from flask import Flask, session
from mentormatch.config import Config
from mentormatch.routes import bp as routes_bp
from mentormatch.matcher import Matcher, PeopleInfo
from mentormatch.models import db


def start_app(is_testing=False):
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    
    if is_testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = Config.TEST_DB_URL
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = Config.DATABASE_URL
        
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Determine if we're doing auth or not
    google_client_id = Config.GOOGLE_CLIENT_ID
    google_client_secret = Config.GOOGLE_CLIENT_SECRET
    auth_enabled = not is_testing and google_client_id and google_client_secret
    app.config["AUTH_ENABLED"] = auth_enabled

    db.init_app(app)

    app.oauth = None
    if auth_enabled:
        try:
            oauth = OAuth(app)
            oauth.register(
                name="google",
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_id=google_client_id,
                client_secret=google_client_secret,
                client_kwargs={"scope": "openid email profile"}, # user information we need from Google
            )
            app.oauth = oauth
        except OAuthError:
            app.config["AUTH_ENABLED"] = False
            logging.warning("Error setting up OAuth, disable auth")

    # Helper function that adds user every time we render a template
    @app.context_processor
    def inject_auth_user():
        return {"current_user": session.get("user")}

    with app.app_context():
        app.people = PeopleInfo(db.session)
        app.matcher = Matcher(app.people)
    app.register_blueprint(routes_bp)
    return app
