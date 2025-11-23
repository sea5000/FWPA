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
from pymongo import MongoClient
from datetime import datetime, timedelta


timer_bp = Blueprint('timer', __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client.bookme


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

    new_session = {
        "user": g.current_user,
        "duration": data.get("duration", 0),
        "subject": data.get("subject", None),
        "mode": data.get("mode", None),
        "timestamp": datetime.utcnow()
    }

    db.sessions.insert_one(new_session)
    return jsonify({"message": "Study session saved"}), 201



# Load study session history
@timer_bp.route('/api/study/sessions', methods=['GET'])
def list_sessions():
    sessions = list(db.sessions.find({"user": g.current_user}))
    for s in sessions:
        s["_id"] = str(s["_id"])
    return jsonify(sessions)



# Total study time (all-time)
@timer_bp.route('/api/study/total', methods=['GET'])
def total_study_time():
    pipeline = [
        {"$match": {"user": g.current_user}},
        {"$group": {"_id": None, "total": {"$sum": "$duration"}}}
    ]
    result = list(db.sessions.aggregate(pipeline))

    total_seconds = result[0]["total"] if result else 0

    return jsonify({"total_seconds": total_seconds})


# Study time for the last 7 days
@timer_bp.route('/api/study/weekly', methods=['GET'])
def weekly_study_time():
    start_date = datetime.utcnow() - timedelta(days=7)

    sessions = list(db.sessions.find({
        "user": g.current_user,
        "timestamp": {"$gte": start_date}
    }))

    total = sum(s["duration"] for s in sessions)

    return jsonify({
        "days": 7,
        "total_seconds": total
    })


# Study time for today only
@timer_bp.route('/api/study/today', methods=['GET'])
def today_study_time():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    sessions = list(db.sessions.find({
        "user": g.current_user,
        "timestamp": {"$gte": today_start}
    }))

    total = sum(s["duration"] for s in sessions)

    return jsonify({
        "date": today_start.strftime("%Y-%m-%d"),
        "total_seconds": total
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