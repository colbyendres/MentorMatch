import flask
import os
from config import Config

bp = flask.Blueprint('main', __name__)

@bp.route("/", methods=["GET"])
def root():
    return flask.redirect(flask.url_for('main.home'))

@bp.route("/home", methods=["GET"])
def home():
    return flask.render_template("home.html")

@bp.route("/match", methods=["GET", "POST"])
def match():
    if flask.request.method == 'POST':
        try:
            matches = flask.current_app.matcher.match()
            total_score = sum([int(triplet[2]) for triplet in matches])
            happiness_score = int(100 * (total_score / (2.0 * len(matches))))
            flask.flash(f'Match found with {happiness_score}% satisfaction', 'success')
            return flask.render_template("match.html", matches=matches)
        except (ValueError) as e:
            flask.flash(str(e), 'error')
            return flask.render_template("match.html", matches=[])
    else:
        matches = flask.current_app.matcher.get_cached_matches()
        if not matches:
            flask.flash('No matching found in cache', 'warning')
        return flask.render_template("match.html", matches=matches)
    
@bp.route("/add", methods=["GET", "POST"])
def add():
    if flask.request.method == 'GET':
        mentors = flask.current_app.people.mentors
        mentees = flask.current_app.people.mentees
        return flask.render_template("add.html", mentors=mentors, mentees=mentees)
    else:
        try:
            name = flask.request.form['name']
            designation = flask.request.form['position']
            prefs = flask.request.form.getlist('matches')
            flask.current_app.people.add_person(name, designation, prefs)
        except (ValueError, TypeError) as e:
            flask.flash(e, 'error')
        except FileNotFoundError:
            flask.flash('Data file not found', 'warning')
        return flask.redirect(flask.url_for('main.home'))

@bp.route("/view", methods=["GET"])
def view():
    people = flask.current_app.people.get_people()
    return flask.render_template("view.html", people=people)

# TODO: Should this really be a GET?
@bp.route("/match/download", methods=["GET"])
def download():
    flask.current_app.matcher.download_match()
    if not os.path.exists(Config.REMOTE_MATCH_FILE):
        flask.flash('Match file does not exist on server: download refused', 'warning')
        return flask.redirect(flask.url_for('main.match'))
    else:
        return flask.send_file(Config.REMOTE_MATCH_FILE, as_attachment=True)
