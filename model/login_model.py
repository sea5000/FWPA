"""
Login model backed by MongoDB (with a small in-memory fallback).

Functions here will attempt to read from the `users` collection in the
`mydatabase` MongoDB instance on localhost. If the DB call fails or the
document is missing, behavior falls back to the (possibly-empty) in-memory
`USERS` if present.
"""
from pymongo import MongoClient
from typing import Optional, Dict, List
import os

# connect lazily/configurable via env var
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
_client = MongoClient(MONGO_URI)
_db = _client.get_database('mydatabase')
_users_col = _db.get_collection('users')


def _doc_to_user(doc: Dict) -> Dict:
    if not doc:
        return None
    # normalize document to expected user dict shape
    return {
        'id': doc.get('id') or str(doc.get('_id')),
        'username': doc.get('username'),
        'email': doc.get('email'),
        # include password only for internal checks; callers should trim it
        'password': doc.get('password')
    }


def get_user_by_username(username: str) -> Optional[Dict]:
    """Return a user document by username, or None if not found."""
    if not username:
        return None
    doc = _users_col.find_one({'username': username})
    if doc:
        return _doc_to_user(doc)

    # fallback: if an in-memory USERS exists, try it
    try:
        from .login_model import USERS as _USERS  # type: ignore
        for u in _USERS:
            if u.get('username') == username:
                return {
                    'id': u.get('id'),
                    'username': u.get('username'),
                    'email': u.get('email'),
                    'password': u.get('password')
                }
    except Exception:
        pass

    return None


def verify_user(username: str, password: str) -> Optional[Dict]:
    """Verify credentials against the users collection.

    Returns a small user dict (no password) on success, or None.
    """
    user = get_user_by_username(username)
    if user and user.get('password') == password:
        return {'id': user['id'], 'username': user['username'], 'email': user.get('email')}
    return None


def get_all_users() -> List[Dict]:
    """Return a list of users (including password field) for admin/debug uses.

    Note: callers should avoid exposing passwords in production.
    """
    docs = list(_users_col.find({}, {'_id': 0}))
    out = []
    for d in docs:
        out.append(_doc_to_user(d))

    # fallback to in-memory list if DB empty
    if not out:
        try:
            from .login_model import USERS as _USERS  # type: ignore
            for u in _USERS:
                out.append({'id': u.get('id'), 'username': u.get('username'), 'email': u.get('email'), 'password': u.get('password')})
        except Exception:
            pass

    return out
