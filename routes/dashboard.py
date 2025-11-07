from flask import Blueprint, render_template, jsonify, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users, get_user_by_username
from model.studyData_model import get_user_study_data

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@dashboard_bp.route('/', endpoint='index')
def dashboard():
    """Protected dashboard route."""
    return render_template(
        'dashboard.html',
        username=g.current_user,
        users=get_all_users(),
        profileData=get_user_by_username(g.current_user),
        studyData=get_user_study_data(g.current_user),
    )


@dashboard_bp.route('/users', endpoint='users')
def dashboard_list_users():
    users = get_all_users()
    return jsonify(users)
