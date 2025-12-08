from flask import Blueprint, render_template, request, g
from utils.auth import get_current_user_from_token, get_pepper_by_version, combine_password_and_pepper, ph, get_current_pepper_version
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
    password=request.form.get('password')
    
    current_version = get_current_pepper_version()
    if not current_version:
        return render_template('signup.html', error='Server not configured properly.', users=get_all_users())
    pepper = get_pepper_by_version(current_version)
    combined = combine_password_and_pepper(password, pepper)

    # Argon2 will automatically salt and produce a safe encoded hash
    password_hash = ph.hash(combined)
    
    if create_user(
        username= request.form.get('username'),
        email=request.form.get('email'),
        password_hash=password_hash,
        pepper_version=current_version,
        name=request.form.get('name')):
        return login_post()
    else:
        return render_template('signup.html', error='Registration failed. Please try again.', users=get_all_users())
