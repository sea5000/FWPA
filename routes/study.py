from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users

study_bp = Blueprint('study', __name__)


@study_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@study_bp.route('/', endpoint='index')
def study_index():
    return render_template('study-dashboard.html', username=g.current_user, users=get_all_users())

@study_bp.route('/study/timer', endpoint='dashboard')
def timer():
    return render_template('study_timer.html', username=g.current_user, users=get_all_users())
