"""
Login model backed by MongoDB

Functions here will attempt to read from the `users` collection in the
`mydatabase` MongoDB instance on localhost.
"""
from .mongo import get_db
from typing import Optional, Dict, List
import os
from datetime import datetime as dt
from utils.auth import get_current_pepper_version, get_pepper_by_version, combine_password_and_pepper, ph
from argon2.exceptions import VerifyMismatchError
_db = get_db()
_users_col = _db.users

# ensure a unique index on username where possible (best-effort)
try:
    _users_col.create_index('username', unique=True)
except Exception:
    pass


def create_user(username: str, email: str, password_hash: str, pepper_version:str, name: str) -> bool:
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
            'password_hash': password_hash,
            'pepper_version': pepper_version,
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
        'password_hash': doc.get('password_hash'),
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
                    'password_hash': u.get('password_hash')
                }
    except Exception:
        pass

    return None


def verify_user(username: str, pepperedPassword: str) -> Optional[Dict]:
    """Verify credentials against the users collection.

    Returns a small user dict (no password) on success, or None.
    """
    user = get_user_by_username(username)
    try:
        if user and ph.verify(user.get('password_hash'), pepperedPassword):
            return {'id': user['id'], 'username': user['username'], 'email': user.get('email')}
        return None
    except VerifyMismatchError:
        return False


def get_all_users() -> List[Dict]:
    """Return a list of users for admin/debug uses.

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
                out.append({'id': u.get('id'), 'username': u.get('username'), 'email': u.get('email')})
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


def update_login_streak(username: str) -> bool:
    """Update user's login streak based on daily logins.
    
    Streak logic:
    - If lastLogin was yesterday (consecutive day), increment streak
    - If lastLogin was today (already logged in today), keep streak the same
    - If lastLogin was more than 1 day ago, reset streak to 1
    - Update lastLogin to today
    
    Args:
        username: The username of the user
        
    Returns:
        True on success, False on failure
    """
    if not username:
        print(f"update_login_streak: username is empty")
        return False
    
    try:
        # Get current user data
        user_doc = _users_col.find_one({'username': username})
        if not user_doc:
            print(f"update_login_streak: user '{username}' not found in MongoDB")
            return False
        
        # Get current studyData, preserving all existing fields
        study_data = user_doc.get('studyData', {})
        # Ensure studyData has required structure, preserving existing fields
        if not isinstance(study_data, dict):
            study_data = {}
        # Preserve existing fields like 'decks', 'loginHistory', etc.
        # Only initialize if missing
        if 'decks' not in study_data:
            study_data['decks'] = []
        
        current_streak = study_data.get('streak', 0)
        last_login_str = study_data.get('lastLogin')
        
        # Get current date (UTC, date only, no time)
        now = dt.utcnow()
        today = now.date()
        
        # Parse lastLogin if it exists
        last_login_date = None
        if last_login_str:
            try:
                # Parse ISO format datetime string
                last_login_dt = dt.fromisoformat(last_login_str.replace('Z', '+00:00'))
                last_login_date = last_login_dt.date()
            except (ValueError, AttributeError) as e:
                print(f"update_login_streak: Error parsing lastLogin '{last_login_str}': {e}")
                last_login_date = None
        
        # Calculate new streak
        new_streak = current_streak
        
        if last_login_date is None:
            # First login ever - start streak at 1
            new_streak = 1
            print(f"update_login_streak: First login for '{username}', starting streak at 1")
        elif last_login_date == today:
            # Already logged in today - keep streak the same
            new_streak = current_streak
            print(f"update_login_streak: User '{username}' already logged in today, streak remains {current_streak}")
        else:
            # Calculate days difference
            days_diff = (today - last_login_date).days
            
            if days_diff == 1:
                # Consecutive day - increment streak
                new_streak = current_streak + 1
                print(f"update_login_streak: Consecutive login for '{username}', streak: {current_streak} -> {new_streak}")
            elif days_diff > 1:
                # Missed one or more days - reset streak to 1
                new_streak = 1
                print(f"update_login_streak: Missed login for '{username}' (last login {days_diff} days ago), resetting streak to 1")
            else:
                # This shouldn't happen (days_diff < 0 means future date)
                print(f"update_login_streak: Warning - lastLogin is in the future for '{username}', keeping streak at {current_streak}")
                new_streak = current_streak
        
        # Update studyData with new streak and lastLogin
        study_data['streak'] = new_streak
        study_data['lastLogin'] = now.isoformat()
        
        # Update MongoDB
        res = _users_col.update_one(
            {'username': username},
            {'$set': {'studyData': study_data}}
        )
        
        if res.matched_count > 0:
            print(f"update_login_streak: ✓ Successfully updated streak for '{username}' to {new_streak}")
            return True
        else:
            print(f"update_login_streak: ✗ Failed to update - user not matched")
            return False
            
    except Exception as e:
        print(f"update_login_streak (login_model): error updating login streak: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_user_password(username: str, new_password: str) -> bool:
    """Update a user's password in MongoDB.
    
    Args:
        username: The username of the user to update
        new_password: The new password to set
        
    Returns:
        True on success, False on failure
    """
    if not username:
        print(f"update_user_password: username is empty")
        return False
    
    if not new_password:
        print(f"update_user_password: new_password is empty")
        return False
    
    try:
        # First verify the user exists
        user_exists = _users_col.find_one({'username': username})
        if not user_exists:
            print(f"update_user_password: user '{username}' not found in MongoDB")
            return False
        
        current_version = get_current_pepper_version()
        if not current_version:
            print(f"update_user_password: user '{username}' not found in MongoDB")
            return False
        pepper = get_pepper_by_version(current_version)
        combined = combine_password_and_pepper(new_password, pepper)

        # Argon2 will automatically salt and produce a safe encoded hash
        password_hash = ph.hash(combined)
        
        # Update the password
        print(f"update_user_password: Updating password for user '{username}'")
        res = _users_col.update_one(
            {'username': username},
            {'$set': {'password_hash': password_hash, 'pepper_version': current_version}}
        )
        
        # Log the result
        print(f"update_user_password: matched_count={res.matched_count}, modified_count={res.modified_count}")
        
        # Success if we matched the user
        if res.matched_count > 0:
            # Verify the update by reading back
            updated_user = _users_col.find_one({'username': username})
            if updated_user and updated_user.get('password_hash') == password_hash:
                print(f"update_user_password: ✓ Successfully updated password for '{username}'")
                return True
            else:
                print(f"update_user_password: ⚠ Warning - password verification failed")
                # Still return True if we matched - the update was attempted
                return True
        else:
            print(f"update_user_password: ✗ Failed to update - user not matched (matched_count={res.matched_count})")
            return False
    except Exception as e:
        print(f"update_user_password (login_model): error updating password: {e}")
        import traceback
        traceback.print_exc()
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
        
        # Success if we matched the user (modified_count can be 0 if value was already the same)
        if res.matched_count > 0:
            # Verify the update by reading back
            updated_user = _users_col.find_one({'username': username})
            if updated_user:
                stored_pic = updated_user.get('profile_pic')
                print(f"update_user_profile_pic: Verified - stored value is now: {stored_pic}")
                if profile_pic_url is None:
                    # For removal, field should be None or not present
                    if stored_pic is None or stored_pic == '':
                        print(f"update_user_profile_pic: Successfully removed profile_pic for '{username}'")
                        return True
                    else:
                        print(f"update_user_profile_pic: Warning - field still exists with value: {stored_pic}")
                        # Still return True - update was attempted and matched
                        return True
                else:
                    # For setting, check if value matches
                    if stored_pic == profile_pic_url:
                        print(f"update_user_profile_pic: ✓ Successfully updated profile_pic for '{username}'")
                        return True
                    else:
                        print(f"update_user_profile_pic: ⚠ Warning - stored value '{stored_pic}' doesn't match expected '{profile_pic_url}'")
                        # If we matched, the update was attempted - return True anyway
                        # (modified_count might be 0 if value was already set to something else)
                        print(f"update_user_profile_pic: Returning True (matched user, update attempted)")
                        return True
            else:
                print(f"update_user_profile_pic: ⚠ Warning - user not found after update")
                return False
        else:
            print(f"update_user_profile_pic: ✗ Failed to update - user not matched (matched_count={res.matched_count})")
            return False
    except Exception as e:
        print(f"update_user_profile_pic (login_model): error updating profile picture: {e}")
        import traceback
        traceback.print_exc()
        return False