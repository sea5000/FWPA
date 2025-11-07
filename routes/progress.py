from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users

progress_bp = Blueprint('progress', __name__)


@progress_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@progress_bp.route('/', endpoint='index')
def progress_index():
    return render_template('progress.html', username=g.current_user, users=get_all_users())
