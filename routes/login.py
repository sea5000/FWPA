from flask import Blueprint, render_template, jsonify, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users

login_bp = Blueprint('login', __name__)


@login_bp.before_request
def require_auth():
    """Set g.current_user or redirect to login."""
    user = get_current_user_from_token()
    # If helper returns a redirect response, just return it
    from flask import redirect
    if not isinstance(user, str):
        return user
    g.current_user = user


@login_bp.route('/', endpoint='index')
def login():
    """Protected login page route that requires JWT authentication."""
    return render_template('login.html', username=g.current_user, users=get_all_users())


@login_bp.route('/users')
def login_list_users():
    """Return a list of all users (without passwords) in JSON format."""
    users = get_all_users()
    return jsonify(users)
