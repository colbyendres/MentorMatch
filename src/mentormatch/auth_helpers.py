from urllib.parse import urljoin, urlparse
import flask

from mentormatch.config import Config

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

def is_admin(user: dict[str]):
    """ Check if the current user is an admin """
    return user['email'] in Config.ADMIN_USERS

def is_auth_enabled():
    """ Check if authentication is enabled """
    return flask.current_app.config.get('AUTH_ENABLED', False)

def is_public_endpoint(endpoint: str):
    """ Check if user requested a public endpoint """
    return endpoint is None or endpoint in PUBLIC_ENDPOINTS

def is_safe_redirect_target(target: str):
    """ Validate redirect link, as to prevent open-redirect vulnerabilities"""
    host_url = urlparse(flask.request.host_url)
    redirect_url = urlparse(urljoin(flask.request.host_url, target))
    return (
        redirect_url.scheme in {'http', 'https'}
        and host_url.netloc == redirect_url.netloc
    )
    
def can_modify_person(current_user: dict[str], target_user: str):
    """ Check if current user has necessary edit privileges for a particular person """
    if not is_auth_enabled() or is_admin(current_user):
        return True 
    user_to_modify = flask.current_app.people.get_from_name(target_user)
    return current_user['email'] == user_to_modify.email
