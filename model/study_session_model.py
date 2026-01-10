"""Study Session Model - Tracks and analyzes user study time in MongoDB.

This module provides functions to:
- Log individual study sessions (duration, subject, mode)
- Retrieve study history for users
- Calculate study statistics (total time, weekly time, today's time)
- Support spaced repetition analytics

All time calculations use MongoDB aggregation pipeline for efficiency.
"""

from datetime import datetime, timedelta
from .mongo import get_db


def log_session(user: str, duration: int, subject: str | None = None, mode: str | None = None, timestamp: datetime | None = None) -> str:
    """Record a completed study session in the database.
    
    Args:
        user: Username of the person studying
        duration: Length of study session in seconds (e.g., 1500 = 25 minutes)
        subject: Topic studied (optional, e.g., "Math", "Biology")
        mode: Study mode/technique (optional, e.g., "Pomodoro", "Deep Work")
        timestamp: When the session occurred (default: current UTC time)
        
    Returns:
        String ID of the newly created session document
        
    Each session is timestamped and can be used for streak tracking and analytics.
    """
    db = get_db()
    # Build document structure for MongoDB insertion
    doc = {
        'user': user,  # Track which user this session belongs to
        'duration': int(duration or 0),  # Ensure duration is an integer
        'subject': subject,  # Can be None
        'mode': mode,  # Can be None
        'timestamp': (timestamp or datetime.utcnow())  # Use provided or current time
    }
    # Insert into sessions collection and get the generated ID
    res = db.study_sessions.insert_one(doc)
    return str(res.inserted_id)


def list_sessions(user: str) -> list[dict]:
    """Retrieve all study sessions for a specific user, newest first.
    
    Args:
        user: Username to retrieve sessions for
        
    Returns:
        List of session dictionaries sorted by timestamp (newest first),
        with ObjectIds converted to strings
    """
    db = get_db()
    # Query sessions for this user and sort by timestamp descending (newest first)
    sessions = list(db.study_sessions.find({'user': user}).sort('timestamp', -1))
    # Convert MongoDB ObjectIds to strings for JSON serialization
    for s in sessions:
        s['_id'] = str(s['_id'])
    return sessions


def total_study_time(user: str) -> int:
    """Calculate total cumulative study time for a user across all sessions.
    
    Args:
        user: Username to calculate total for
        
    Returns:
        Total study time in seconds (integer)
        
    Uses MongoDB aggregation pipeline for efficient calculation:
    - $match: Filter to only this user's sessions
    - $group: Sum all duration values
    """
    db = get_db()
    # MongoDB aggregation pipeline for efficient server-side calculation
    pipeline = [
        {'$match': {'user': user}},  # Filter documents: only this user
        {'$group': {'_id': None, 'total': {'$sum': '$duration'}}}  # Sum all durations
    ]
    result = list(db.study_sessions.aggregate(pipeline))
    # Return the sum, or 0 if no sessions exist
    return int(result[0]['total']) if result else 0


def time_since(user: str, since: datetime) -> int:
    """Calculate total study time since a specific date/time.
    
    Args:
        user: Username to calculate for
        since: Datetime boundary (inclusive) - includes sessions from this time forward
        
    Returns:
        Total seconds studied since the given time
        
    Uses MongoDB query with timestamp comparison: timestamp >= since
    """
    db = get_db()
    # Query for sessions after the given timestamp and sum their durations
    # $gte: Greater than or equal (includes the start time)
    docs = db.study_sessions.find({'user': user, 'timestamp': {'$gte': since}})
    # Sum durations manually (could use aggregation for very large datasets)
    return int(sum(d.get('duration', 0) for d in docs))


def weekly_study_time(user: str, days: int = 7) -> int:
    """Calculate total study time for the last N days (default 7 days).
    
    Args:
        user: Username to calculate for
        days: Number of days to look back (default 7 for one week)
        
    Returns:
        Total seconds studied in the last N days
    """
    # Calculate the start time: N days ago from now
    start = datetime.utcnow() - timedelta(days=days)
    # Delegate to time_since for actual calculation
    return time_since(user, start)


def today_study_time(user: str) -> int:
    """Calculate total study time for today only (since midnight UTC).
    
    Args:
        user: Username to calculate for
        
    Returns:
        Total seconds studied today (from 00:00:00 UTC to now)
    """
    # Get today's start (midnight UTC, no time component)
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    # Delegate to time_since for actual calculation
    return time_since(user, start)
