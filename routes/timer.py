"""from flask import Blueprint, render_template, g
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
    return jsonify({'message': 'Session logged'}), 201"""


from flask import Blueprint, render_template, g, request, jsonify
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from model.study_session_model import (
    log_session,
    list_sessions,
    total_study_time,
    weekly_study_time,
    today_study_time
)
from datetime import datetime, timedelta


timer_bp = Blueprint('timer', __name__)


# REQUIRE AUTH BEFORE REQUESTS
@timer_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user         # redirect/abort
    g.current_user = user


# TIMER PAGE
@timer_bp.route('/', endpoint='index')
def timer_index():
    return render_template(
        'timer.html',
        username=g.current_user,
        users=get_all_users()
    )



# Create / Log a study session
@timer_bp.route('/api/study/sessions', methods=['POST'])
def log_study_session():
    """
    Expected JSON:
    {
        "duration": 1500,          # seconds
        "subject": "Math",         # optional
        "mode": "Pomodoro"         # optional
    }
    """
    data = request.get_json()
    duration = data.get("duration", 0)
    subject = data.get("subject", None)
    mode = data.get("mode", None)
    
    session_id = log_session(g.current_user, duration, subject, mode)
    return jsonify({"message": "Study session saved", "session_id": session_id}), 201



# Load study session history
@timer_bp.route('/api/study/sessions', methods=['GET'])
def list_sessions_endpoint():
    sessions = list_sessions(g.current_user)
    return jsonify(sessions)



# Total study time (all-time)
@timer_bp.route('/api/study/total', methods=['GET'])
def total_study_time_endpoint():
    total_seconds = total_study_time(g.current_user)
    return jsonify({"total_seconds": total_seconds})


# Study time for the last 7 days
@timer_bp.route('/api/study/weekly', methods=['GET'])
def weekly_study_time_endpoint():
    total_seconds = weekly_study_time(g.current_user, days=7)
    return jsonify({
        "days": 7,
        "total_seconds": total_seconds
    })


# Study time for today only
@timer_bp.route('/api/study/today', methods=['GET'])
def today_study_time_endpoint():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_seconds = today_study_time(g.current_user)
    return jsonify({
        "date": today_start.strftime("%Y-%m-%d"),
        "total_seconds": total_seconds
    })


study_session = [
    {
        "user": "alice",
        "duration": 1500,
        "subject": "Math",
        "mode": "Pomodoro",
        "timestamp": datetime.utcnow() - timedelta(days=1)
    },
    {
        "user": "alice",
        "duration": 3000,
        "subject": "Science",
        "mode": "Deep Work",
        "timestamp": datetime.utcnow() - timedelta(days=2)
    },
    {
        "user": "bob",
        "duration": 1200,
        "subject": "History",
        "mode": "Pomodoro",
        "timestamp": datetime.utcnow() - timedelta(hours=5)
    },
]