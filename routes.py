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
        mentors, mentees = flask.current_app.people.get_people_without_prefs()
        return flask.render_template("add.html", mentors=mentors, mentees=mentees)
    else:
        try:
            name = flask.request.form['name']
            designation = flask.request.form['position']
            prefs = flask.request.form.getlist('matches')
            flask.current_app.people.add_person(name, designation, prefs)
            flask.flash(f'Added {designation} {name} to MentorMatch', 'success')
        except (ValueError, TypeError) as e:
            flask.flash(e, 'error')
        return flask.redirect(flask.url_for('main.home'))

@bp.route("/view", methods=["GET"])
def view():
    people = flask.current_app.people.get_people_with_prefs()
    print(people)
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

@bp.route("/edit/<string:user_name>", methods=["GET", "POST"])
def edit(user_name):
    if flask.request.method == "GET":
        is_mentor = flask.request.args.get('is_mentor').lower() == 'true'
        mentors, mentees = flask.current_app.people.get_people_without_prefs()
        return flask.render_template("edit.html", name=user_name, is_mentor=is_mentor, mentors=mentors, mentees=mentees)
    else:
        new_name = flask.request.form['name']
        new_is_mentor = flask.request.form['position'] == 'mentor'
        new_prefs = flask.request.form.getlist('matches')
        old_name = user_name # TODO: Fix this, since name is editable
        try:
            flask.current_app.people.edit_person(old_name, new_name, new_is_mentor, new_prefs)
            flask.flash('Profile updated', 'success')
        except Exception as e:
            flask.flash(str(e), 'error')
            raise e
        return flask.redirect(flask.url_for('main.home'))
    
@bp.route("/delete/<string:user_name>", methods=["POST"])
def delete(user_name):
    try:
        flask.current_app.people.delete_person(user_name)
        flask.flash(f'Person {user_name} deleted', 'success')
    except Exception as e:
        flask.flash(str(e), 'error')
    return flask.redirect(flask.url_for('main.home'))
