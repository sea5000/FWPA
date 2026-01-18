"""Timer Routes - Pomodoro timer and study session tracking endpoints.

This module provides Flask routes for the study timer feature:
- GET /timer/: Display Pomodoro timer page
- POST /timer/api/study/sessions: Log a completed study session
- GET /timer/api/study/sessions: Get user's session history
- GET /timer/api/study/total: Get total all-time study time
- GET /timer/api/study/weekly: Get study time for last 7 days
- GET /timer/api/study/today: Get study time for today only

The timer tracks study sessions in MongoDB for analytics and streaks.
All routes require JWT authentication.
"""

from flask import Blueprint, render_template, g, request, jsonify
from utils.auth import get_current_user_from_token  # JWT authentication
from model.login_model import get_all_users  # Get user list for templates
from model.studyData_model import get_user_study_data
from model.study_session_model import (
    log_session,  # Insert session into database
    list_sessions,  # Get user's session history
    total_study_time,  # Calculate total time
    weekly_study_time,  # Calculate weekly time
    today_study_time  # Calculate today's time
)
from datetime import datetime, timedelta


timer_bp = Blueprint('timer', __name__)


# ============================================================================
# AUTHENTICATION MIDDLEWARE
# ============================================================================

# REQUIRE AUTH BEFORE REQUESTS
@timer_bp.before_request
def require_auth():
    """Before-request hook: Verify JWT token for all timer routes.
    
    This runs before every route in this blueprint.
    Stores authenticated username in g.current_user for use in handlers.
    """
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user  # Return redirect to login if authentication failed
    g.current_user = user


# ============================================================================
# PAGE ROUTES
# ============================================================================

# TIMER PAGE
@timer_bp.route('/', endpoint='index')
def timer_index():
    """Display the Pomodoro timer page.
    
    GET /timer/
    
    Returns:
        HTML template with timer interface and user list for social features
    """
    return render_template(
        'timer.html',
        username=g.current_user,
        users=get_all_users(),  # Pass all users for potential friend features
        studyData=get_user_study_data(g.current_user),
    )


# ============================================================================
# API ROUTES - SESSION LOGGING AND RETRIEVAL
# ============================================================================

# Create / Log a study session
@timer_bp.route('/api/study/sessions', methods=['POST'])
def log_study_session():
    """Log a completed study session to the database.
    
    POST /timer/api/study/sessions
    
    Expected JSON body:
    {
        "duration": 1500,          # seconds (required) - e.g., 1500 = 25 min
        "subject": "Math",         # optional - what was studied
        "mode": "Pomodoro"         # optional - timer mode used
    }
    
    Returns:
        201 Created with session_id of the newly logged session
        
    Sessions are tracked for:
    - Streak calculation (daily logins)
    - Study time analytics
    - Performance tracking
    - Goal monitoring
    """
    data = request.get_json()
    duration = data.get("duration", 0)  # Get duration in seconds
    subject = data.get("subject", None)  # Get subject (optional)
    mode = data.get("mode", None)  # Get timer mode (optional)
    
    # Call model to insert session into MongoDB
    session_id = log_session(g.current_user, duration, subject, mode)
    return jsonify({"message": "Study session saved", "session_id": session_id}), 201


# Load study session history
@timer_bp.route('/api/study/sessions', methods=['GET'])
def list_sessions_endpoint():
    """Retrieve all study sessions for the current user.
    
    GET /timer/api/study/sessions
    
    Returns:
        JSON array of session objects, sorted by newest first
        Each session includes: user, duration, subject, mode, timestamp, _id
    """
    sessions = list_sessions(g.current_user)
    return jsonify(sessions)


# ============================================================================
# API ROUTES - STUDY TIME STATISTICS
# ============================================================================

# Total study time (all-time)
@timer_bp.route('/api/study/total', methods=['GET'])
def total_study_time_endpoint():
    """Calculate total cumulative study time for the user across all sessions.
    
    GET /timer/api/study/total
    
    Returns:
        JSON with total_seconds: Total seconds studied (integer)
        
    Example response: {"total_seconds": 432000}  (120 hours)
    """
    total_seconds = total_study_time(g.current_user)
    return jsonify({"total_seconds": total_seconds})


# Study time for the last 7 days
@timer_bp.route('/api/study/weekly', methods=['GET'])
def weekly_study_time_endpoint():
    """Calculate total study time for the past 7 days.
    
    GET /timer/api/study/weekly
    
    Returns:
        JSON with:
        - days: Number of days (7)
        - total_seconds: Total seconds studied in last 7 days
        
    Example response: {"days": 7, "total_seconds": 43200}  (12 hours/week)
    """
    total_seconds = weekly_study_time(g.current_user, days=7)
    return jsonify({
        "days": 7,
        "total_seconds": total_seconds
    })


# Study time for today only
@timer_bp.route('/api/study/today', methods=['GET'])
def today_study_time_endpoint():
    """Calculate total study time for today (since midnight UTC).
    
    GET /timer/api/study/today
    
    Returns:
        JSON with:
        - date: Today's date in YYYY-MM-DD format
        - total_seconds: Seconds studied today
        
    Example response: {"date": "2025-12-08", "total_seconds": 5400}  (1.5 hours)
    
    Used for:
    - Daily streak tracking (minimum study time requirement)
    - Daily goals checking
    - Habit formation monitoring
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total_seconds = today_study_time(g.current_user)
    return jsonify({
        "date": today_start.strftime("%Y-%m-%d"),
        "total_seconds": total_seconds
    })


# ============================================================================
# SAMPLE DATA (for testing/documentation)
# ============================================================================

# Example study sessions (shows structure for reference)
study_session = [
    {
        "user": "alice",
        "duration": 1500,  # 25 minutes (Pomodoro)
        "subject": "Math",
        "mode": "Pomodoro",
        "timestamp": datetime.utcnow() - timedelta(days=1)
    },
    {
        "user": "alice",
        "duration": 3000,  # 50 minutes (Deep Work)
        "subject": "Science",
        "mode": "Deep Work",
        "timestamp": datetime.utcnow() - timedelta(days=2)
    },
    {
        "user": "bob",
        "duration": 1200,  # 20 minutes (Pomodoro)
        "subject": "History",
        "mode": "Pomodoro",
        "timestamp": datetime.utcnow() - timedelta(hours=5)
    },
]