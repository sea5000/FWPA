from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users

signup_bp = Blueprint('signup', __name__)


# @signup_bp.before_request
# def require_auth():
#     user = get_current_user_from_token()
#     if not isinstance(user, str):
#         return user
#     g.current_user = user


@signup_bp.route('/', endpoint='index')
def signup_index():
    return render_template('signup.html')
