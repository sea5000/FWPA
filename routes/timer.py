from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from flask import request, jsonify
from pymongo import MongoClient

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

from datetime import datetime
from flask import request, jsonify
@timer_bp.route('/api/study/sessions', methods=['POST'])
def log_study_session():
    session_data = request.get_json()
    session_data['user'] = g.current_user
    session_data['date'] = datetime.now().strftime('%Y-%m-%d')
    db.sessions.insert_one(session_data)
    return jsonify({'message': 'Session logged'}), 201