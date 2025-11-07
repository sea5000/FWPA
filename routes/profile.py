from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users, get_user_by_username

profile_bp = Blueprint('profile', __name__)


@profile_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@profile_bp.route('/', endpoint='index')
def profile_index():
    return render_template('profile-settings.html', username=g.current_user, users=get_all_users(), profileData=get_user_by_username(g.current_user))
