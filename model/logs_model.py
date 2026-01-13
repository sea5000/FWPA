from datetime import datetime
from .mongo import get_db
from typing import Optional, Dict, Any, List

_db = get_db()
_logs_col = _db.ai_generation_logs


def insert_ai_log(user: str, deck_id: Optional[str], prompt: str, raw_response: str, parsed: Optional[Dict[str, Any]] = None, feedback: Optional[str] = None, success: bool = True, extra: Optional[Dict[str, Any]] = None) -> str:
    """Insert a log entry into the `ai_generation_logs` collection.

    Returns the inserted document id as a string.
    """
    doc = {
        'user': user,
        'deck_id': str(deck_id) if deck_id is not None else None,
        'prompt': prompt,
        'raw_response': raw_response,
        'parsed': parsed or {},
        'feedback': feedback,
        'success': bool(success),
        'extra': extra or {},
        'created_at': datetime.utcnow().isoformat(),
    }
    res = _logs_col.insert_one(doc)
    return str(res.inserted_id)


def find_logs(filter: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Query recent logs. Returns list of documents (JSON-serializable)."""
    q = filter or {}
    docs = list(_logs_col.find(q).sort('created_at', -1).limit(limit))
    for d in docs:
        d['_id'] = str(d.get('_id'))
    return docs
