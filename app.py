from flask import Flask
from config import Config
from routes import bp as routes_bp
from matcher import Matcher, PeopleInfo
 
def start_app():    
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    with app.app_context():
        app.people = PeopleInfo(Config.LOCAL_FILE_PATH)
        app.matcher = Matcher(app.people)
    app.register_blueprint(routes_bp)
    return app

flask_app = start_app()
