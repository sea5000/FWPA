"""Friends Routes - Display community members and user profiles.

This module provides Flask routes for the friends/community feature:
- GET /friends/: Display all users in the community with their profile data

Features:
- Shows all registered users
- Displays profile pictures, streaks, bios
- Allows viewing user profiles
- Enable potential follow/friend features

All routes require JWT authentication.
"""

from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token  # JWT authentication
from model.mongo import get_db  # Direct database access to get all users

friends_bp = Blueprint('friends', __name__)


# ============================================================================
# AUTHENTICATION MIDDLEWARE
# ============================================================================

@friends_bp.before_request
def require_auth():
    """Before-request hook: Verify JWT token for all friends routes.
    
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

@friends_bp.route('/', endpoint='index')
def friends_index():
    """Display the friends/community page with all users.
    
    GET /friends/
    
    Fetches all users from the database and displays them with:
    - Profile picture
    - Username
    - Display name
    - Email
    - Streak count (daily login streak)
    - Bio/About section
    - Study statistics
    - Actions (follow, view profile, message)
    
    Returns:
        HTML template with list of all community members
    """
    db = get_db()
    # Get all users with their full profile data from MongoDB
    all_users = list(db.users.find({}))
    
    # Convert MongoDB ObjectIds to strings for JSON/template compatibility
    # ObjectId is a binary type that can't be serialized to JSON
    for user in all_users:
        user['_id'] = str(user['_id'])
    
    # Render template with current user and all community members
    return render_template(
        'friends.html',
        username=g.current_user,  # Current logged-in user
        users=all_users  # All users in the community
    )
