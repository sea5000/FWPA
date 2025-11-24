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
from datetime import datetime as dt

# connect lazily/configurable via env var
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
_client = MongoClient(MONGO_URI)
_db = _client.get_database('mydatabase')
_users_col = _db.get_collection('users')

# ensure a unique index on username where possible (best-effort)
try:
    _users_col.create_index('username', unique=True)
except Exception:
    pass


def create_user(username: str, email: str, password: str, name: str) -> bool:
    """Create a new user in the users collection.

    Returns True on success, False on failure (duplicate username, DB error, or invalid input).
    Note: password is stored as provided (no hashing yet).
    """
    if not username:
        return False

    try:
        existing = _users_col.find_one({'username': username})
    except Exception as e:
        print(f"create_user (login_model): error checking existing user: {e}")
        return False

    if existing:
        return False

    try:
        nid = str(_users_col.estimated_document_count() + 1)
        user_doc = {
            'id': nid,
            'username': username,
            'password': password,
            'name': name,
            'email': email,
            # store ISO string for timestamps to avoid datetime/tz handling issues
            'studyData': {'streak': 0, 'lastLogin': dt.utcnow().isoformat(), 'decks': []}
        }
        res = _users_col.insert_one(user_doc)
        print(f"create_user (login_model): inserted user with id {nid}")
        return bool(getattr(res, 'inserted_id', None))
    except Exception as e:
        print(f"create_user (login_model): error inserting user: {e}")
        return False


def _doc_to_user(doc: Dict) -> Dict:
    if not doc:
        return None
    # normalize document to expected user dict shape
    # provide safe defaults so templates don't break when DB was reinitialized
    username = doc.get('username')
    name = doc.get('name') or username
    email = doc.get('email')
    profile_pic = doc.get('profile_pic') if doc.get('profile_pic') else None
    studyData = doc.get('studyData') or {'streak': 0, 'lastLogin': None, 'decks': []}

    return {
        'id': doc.get('id') or str(doc.get('_id')),
        'username': username,
        'name': name,
        'email': email,
        'profile_pic': profile_pic,
        # include password only for internal checks; callers should trim it
        'password': doc.get('password'),
        'studyData': studyData,
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

def delete_user_by_username(username: str) -> bool:
    """Delete a user by username. Returns True if a user was deleted, False otherwise."""
    if not username:
        return False
    try:
        res = _users_col.delete_one({'username': username})
        return res.deleted_count > 0
    except Exception as e:
        print(f"delete_user_by_username (login_model): error deleting user: {e}")
        return False


def update_user_profile_pic(username: str, profile_pic_url: Optional[str]) -> bool:
    """Update a user's profile_pic field in MongoDB.
    
    Args:
        username: The username of the user to update
        profile_pic_url: The URL/path to the profile picture, or None to remove it
        
    Returns:
        True on success, False on failure
    """
    if not username:
        print(f"update_user_profile_pic: username is empty")
        return False
    
    try:
        # First verify the user exists
        user_exists = _users_col.find_one({'username': username})
        if not user_exists:
            print(f"update_user_profile_pic: user '{username}' not found in MongoDB")
            return False
        
        if profile_pic_url is None:
            # Remove the profile_pic field
            print(f"update_user_profile_pic: Removing profile_pic for user '{username}'")
            res = _users_col.update_one(
                {'username': username},
                {'$unset': {'profile_pic': ''}}
            )
        else:
            # Set or update the profile_pic field
            print(f"update_user_profile_pic: Setting profile_pic='{profile_pic_url}' for user '{username}'")
            res = _users_col.update_one(
                {'username': username},
                {'$set': {'profile_pic': profile_pic_url}}
            )
        
        # Log the result
        print(f"update_user_profile_pic: matched_count={res.matched_count}, modified_count={res.modified_count}")
        
        # Success if we matched the user (even if value was already the same)
        if res.matched_count > 0:
            # Verify the update actually happened
            updated_user = _users_col.find_one({'username': username})
            if updated_user:
                stored_pic = updated_user.get('profile_pic')
                if profile_pic_url is None:
                    # For removal, check that field is gone or None
                    if stored_pic is None or stored_pic == '':
                        print(f"update_user_profile_pic: Successfully removed profile_pic for '{username}'")
                        return True
                else:
                    # For setting, check that value matches
                    if stored_pic == profile_pic_url:
                        print(f"update_user_profile_pic: Successfully updated profile_pic for '{username}'")
                        return True
                    else:
                        print(f"update_user_profile_pic: Warning - stored value '{stored_pic}' doesn't match expected '{profile_pic_url}'")
            
        print(f"update_user_profile_pic: Failed to update - matched_count={res.matched_count}")
        return False
    except Exception as e:
        print(f"update_user_profile_pic (login_model): error updating profile picture: {e}")
        import traceback
        traceback.print_exc()
        return False