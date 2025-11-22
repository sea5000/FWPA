from flask import Blueprint, render_template, request, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from model.login_model import create_user
from .auth_routes import auth_bp, login_post
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
@signup_bp.route('/signup', endpoint='signup', methods=['POST'])
def signup_register():
    # Handle user registration logic here
    # allow username to be optional; fall back to email if not provided
       
    if create_user(
        username= request.form.get('username'),
        email=request.form.get('email'),
        password=request.form.get('password'),
        name=request.form.get('name')):
        return login_post()
    else:
        return render_template('signup.html', error='Registration failed. Please try again.', users=get_all_users())
