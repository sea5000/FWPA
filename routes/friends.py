from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users

friends_bp = Blueprint('friends', __name__)


@friends_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@friends_bp.route('/', endpoint='index')
def friends_index():
    return render_template('friends.html', username=g.current_user, users=get_all_users())
