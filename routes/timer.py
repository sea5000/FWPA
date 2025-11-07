from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users

timer_bp = Blueprint('timer', __name__)


@timer_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@timer_bp.route('/', endpoint='index')
def timer_index():
    return render_template('timer.html', username=g.current_user, users=get_all_users())
