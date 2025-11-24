from datetime import datetime, timedelta
from .mongo import get_db


def log_session(user: str, duration: int, subject: str | None = None, mode: str | None = None, timestamp: datetime | None = None) -> str:
    db = get_db()
    doc = {
        'user': user,
        'duration': int(duration or 0),
        'subject': subject,
        'mode': mode,
        'timestamp': (timestamp or datetime.utcnow())
    }
    res = db.sessions.insert_one(doc)
    return str(res.inserted_id)


def list_sessions(user: str) -> list[dict]:
    db = get_db()
    sessions = list(db.sessions.find({'user': user}).sort('timestamp', -1))
    for s in sessions:
        s['_id'] = str(s['_id'])
    return sessions


def total_study_time(user: str) -> int:
    db = get_db()
    pipeline = [
        {'$match': {'user': user}},
        {'$group': {'_id': None, 'total': {'$sum': '$duration'}}}
    ]
    result = list(db.sessions.aggregate(pipeline))
    return int(result[0]['total']) if result else 0


def time_since(user: str, since: datetime) -> int:
    db = get_db()
    docs = db.sessions.find({'user': user, 'timestamp': {'$gte': since}})
    return int(sum(d.get('duration', 0) for d in docs))


def weekly_study_time(user: str, days: int = 7) -> int:
    start = datetime.utcnow() - timedelta(days=days)
    return time_since(user, start)


def today_study_time(user: str) -> int:
    start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return time_since(user, start)
