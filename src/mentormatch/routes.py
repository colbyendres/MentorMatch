import flask
import os
from urllib.parse import urljoin, urlparse
from mentormatch.config import Config

bp = flask.Blueprint('main', __name__)

# Resources unauthorized users can access, assuming auth in place
PUBLIC_ENDPOINTS = {
    'main.root',
    'main.home',
    'main.login',
    'main.login_google',
    'main.login_callback',
    'main.logout',
    'static',
}


def _is_safe_redirect_target(target):
    host_url = urlparse(flask.request.host_url)
    redirect_url = urlparse(urljoin(flask.request.host_url, target))
    return (
        redirect_url.scheme in {'http', 'https'}
        and host_url.netloc == redirect_url.netloc
    )


@bp.before_app_request
def ensure_authorized_user():
    """ Ensure that the user has permission to access particular resource """
    
    # Auth is disabled, early return
    if not flask.current_app.config.get('AUTH_ENABLED', False):
        return

    # User requested public endpoint, no need for auth
    endpoint = flask.request.endpoint
    if endpoint is None or endpoint in PUBLIC_ENDPOINTS:
        return

    # User exists and is authenticated
    if flask.session.get('user'):
        return

    # If we've reached this point, the does not have the proper authentication
    # Stash the requested page in the session, so we can redirect there after auth
    if flask.request.method == 'GET':
        flask.session['next_url'] = flask.request.url

    flask.flash('Please sign in to continue', 'warning')
    return flask.redirect(flask.url_for('main.login'))


@bp.route("/", methods=["GET"])
def root():
    return flask.redirect(flask.url_for('main.home'))


@bp.route("/home", methods=["GET"])
def home():
    return flask.render_template("home.html")


@bp.route("/match", methods=["POST"])
def match():
    try:
        force_rematch = flask.request.args.get('force_rematch', False) == 'true'
        matches = flask.current_app.matcher.match(force_rematch)
        total_score = sum(int(triplet[2]) for triplet in matches)
        happiness_score = int(100 * (total_score / (2.0 * len(matches))))
        flask.flash(
            f'Match found with {happiness_score}% satisfaction', 'success')
        return flask.render_template("match.html", matches=matches)
    except (ValueError) as e:
        flask.flash(str(e), 'error')
        return flask.render_template("match.html", matches=[])


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
            email = flask.session.get('user', {})['email']
            flask.current_app.people.add_person(name, designation, prefs, email)
            flask.flash(
                f'Added {designation} {name} to MentorMatch', 'success')
        except (ValueError, TypeError) as e:
            flask.flash(e, 'error')
        return flask.redirect(flask.url_for('main.home'))


@bp.route("/view", methods=["GET"])
def view():
    people = flask.current_app.people.get_people_with_prefs()
    return flask.render_template("view.html", people=people)

@bp.route("/login", methods=["GET"])
def login():
    if flask.session.get('user'):
        return flask.redirect(flask.url_for('main.home'))
    return flask.render_template(
        'login.html',
        auth_enabled=flask.current_app.config.get('AUTH_ENABLED', False),
    )


@bp.route('/login/google', methods=['GET'])
def login_google():
    if not flask.current_app.config.get('AUTH_ENABLED', False):
        flask.flash('Google login is not configured on this server', 'warning')
        return flask.redirect(flask.url_for('main.login'))

    redirect_uri = flask.url_for('main.login_callback', _external=True)
    return flask.current_app.oauth.google.authorize_redirect(redirect_uri)


@bp.route('/login/callback', methods=['GET'])
def login_callback():
    if not flask.current_app.config.get('AUTH_ENABLED', False):
        return flask.redirect(flask.url_for('main.home'))

    try:
        token = flask.current_app.oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            user_info = flask.current_app.oauth.google.parse_id_token(token)
    except (KeyError, TypeError, ValueError):
        flask.flash('Unable to sign in with Google', 'error')
        return flask.redirect(flask.url_for('main.login'))

    flask.session['user'] = {
        'email': user_info.get('email'),
        'name': user_info.get('name'),
        'picture': user_info.get('picture'),
    }

    next_url = flask.session.pop('next_url', None)
    if next_url and _is_safe_redirect_target(next_url):
        return flask.redirect(next_url)

    return flask.redirect(flask.url_for('main.home'))


@bp.route('/logout', methods=['GET'])
def logout():
    flask.session.pop('user', None)
    flask.session.pop('next_url', None)
    return flask.redirect(flask.url_for('main.home'))

@bp.route("/match/download", methods=["GET"])
def download():
    flask.current_app.matcher.download_match()
    if not os.path.exists(Config.REMOTE_MATCH_FILE):
        flask.flash(
            'Match file does not exist on server: download refused', 'warning')
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
        old_name = user_name  # TODO: Fix this, since name is editable
        try:
            flask.current_app.people.edit_person(
                old_name, new_name, new_is_mentor, new_prefs)
            flask.flash('Profile updated', 'success')
        except Exception as e:
            flask.flash(str(e), 'error')
            flask.redirect(flask.url_for('main.home'), code=404)
        return flask.redirect(flask.url_for('main.home'))


@bp.route("/delete/<string:user_name>", methods=["POST"])
def delete(user_name):
    try:
        flask.current_app.people.delete_person(user_name)
        flask.flash(f'Person {user_name} deleted', 'success')
    except Exception as e:
        flask.flash(str(e), 'error')
        flask.redirect(flask.url_for('main.home'), code=404)
    return flask.redirect(flask.url_for('main.home'))
