from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.mongo import get_db

friends_bp = Blueprint('friends', __name__)


@friends_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@friends_bp.route('/', endpoint='index')
def friends_index():
    db = get_db()
    # Get all users with their full profile data
    all_users = list(db.users.find({}))
    for user in all_users:
        user['_id'] = str(user['_id'])
    return render_template('friends.html', username=g.current_user, users=all_users)
