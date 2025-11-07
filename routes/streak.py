from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users

streak_bp = Blueprint('streak', __name__)


@streak_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@streak_bp.route('/', endpoint='index')
def streak_index():
    return render_template('streak.html', username=g.current_user, users=get_all_users())
