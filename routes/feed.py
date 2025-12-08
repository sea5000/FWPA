"""Feed Routes - Social media feed endpoints (posts, likes, comments).

This module provides Flask routes for the social feed feature:
- GET /feed/: Display feed page
- GET /api/feed/posts: Fetch all posts (enriched with author profile pics)
- POST /api/feed/posts: Create new post
- GET /api/feed/posts/<id>: Get single post with comments
- POST /api/feed/posts/<id>/like: Like a post
- POST /api/feed/posts/<id>/comments: Add comment to post

All routes require JWT authentication.
"""

from flask import Blueprint, request, jsonify, render_template, g
from datetime import datetime
from utils.auth import get_current_user_from_token  # Get current user from JWT token
from model.login_model import get_user_by_username  # Get user profile data
from model.feed_post_model import (
    list_posts,
    get_post,
    create_post,
    like_post,
    add_comment,
)

feed_bp = Blueprint("feed", __name__)


# ============================================================================
# AUTHENTICATION MIDDLEWARE
# ============================================================================

# Authentication for every request
@feed_bp.before_request
def require_auth():
    """Before-request hook: Verify JWT token and store user in g.current_user.
    
    This runs before every route in this blueprint.
    If token is invalid, it returns a redirect to login page.
    If token is valid, the username is stored in Flask's g object for this request.
    """
    user = get_current_user_from_token()  # Returns username (str) or redirect response
    if not isinstance(user, str):
        return user  # Return redirect if authentication failed
    g.current_user = user  # Store username for use in route handlers


# ============================================================================
# PAGE ROUTES
# ============================================================================

# FEED PAGE
@feed_bp.route("/", endpoint="index")
def feed_page():
    """Render the feed page template with user profile data.
    
    GET /feed/
    
    Returns:
        HTML template with current user's profile data loaded for display
    """
    # Fetch the full profile data for the current user from MongoDB
    profile_data = get_user_by_username(g.current_user)
    # Pass the profile data to the template so user can see their avatar/name
    return render_template(
        "feed.html", username=g.current_user, profileData=profile_data
    )


# ============================================================================
# API ROUTES - POST OPERATIONS
# ============================================================================

# GET ALL POSTS
@feed_bp.route("/api/feed/posts", methods=["GET"])
def get_posts():
    """Fetch all posts from the feed.
    
    GET /api/feed/posts
    
    Returns JSON array of all posts with:
    - _id, author, text, image, likes, views, comments, timestamp
    - author_profile_pic (enriched from user profiles)
    
    Posts are sorted by newest first (timestamp descending).
    """
    posts = list_posts()  # Get all posts from model layer
    # Enrich posts with author profile pictures from user collection
    for p in posts:
        author = p.get("author")
        if author:
            # Look up user profile for this post's author
            u = get_user_by_username(author)
            if u and u.get("profile_pic"):
                # Add author's profile picture URL to the post
                p["author_profile_pic"] = u["profile_pic"]
    return jsonify(posts)


# CREATE NEW POST
@feed_bp.route("/api/feed/posts", methods=["POST"])
def create_post_endpoint():
    """Create a new post in the feed.
    
    POST /api/feed/posts
    
    Expected JSON body:
    {
        "text": "Post content here",
        "image": "data:image/png;base64,..." (optional)
    }
    
    Returns:
        201 Created with post_id in response
    """
    data = request.get_json()
    text = data.get("text", "")  # Get post text, default to empty string
    image = data.get("image", None)  # Get image (can be None)
    # Call model to insert post into database
    post_id = create_post(g.current_user, text, image)
    # Return success response with the new post's ID
    return jsonify({"message": "Post created", "post_id": post_id}), 201


# ============================================================================
# API ROUTES - SINGLE POST OPERATIONS
# ============================================================================

# GET SINGLE POST (with comments)
@feed_bp.route("/api/feed/posts/<post_id>", methods=["GET"])
def get_single_post(post_id):
    """Fetch a single post by ID, including all comments.
    
    GET /api/feed/posts/{post_id}
    
    Returns:
        Post object with enriched profile pictures for author and all commenters
        404 if post not found
    """
    post = get_post(post_id)  # Fetch post from database
    if not post:
        return jsonify({"error": "Not found"}), 404
    
    # Enrich main post author with profile picture
    author = post.get("author")
    if author:
        u = get_user_by_username(author)
        if u and u.get("profile_pic"):
            post["author_profile_pic"] = u["profile_pic"]
    
    # Enrich each comment's author with profile picture
    comments = post.get("comments") or []
    for c in comments:
        ca = c.get("author")
        if ca:
            cu = get_user_by_username(ca)  # Get commenter's profile
            if cu and cu.get("profile_pic"):
                c["author_profile_pic"] = cu["profile_pic"]  # Add their avatar
    
    return jsonify(post)


# LIKE POST
@feed_bp.route("/api/feed/posts/<post_id>/like", methods=["POST"])
def like_post_endpoint(post_id):
    """Increment the like count on a post by 1.
    
    POST /api/feed/posts/{post_id}/like
    
    Returns:
        200 OK with success message
        404 if post not found
    """
    success = like_post(post_id)  # Call model to increment likes
    if not success:
        return jsonify({"error": "Post not found"}), 404
    return jsonify({"message": "Liked"}), 200


# ADD COMMENT
@feed_bp.route("/api/feed/posts/<post_id>/comments", methods=["POST"])
def add_comment_endpoint(post_id):
    """Add a comment to a post.
    
    POST /api/feed/posts/{post_id}/comments
    
    Expected JSON body:
    {
        "text": "Great post!"
    }
    
    Returns:
        201 Created with success message
        404 if post not found
    """
    data = request.get_json()
    text = data.get("text", "")  # Get comment text
    # Call model to add comment to the post
    success = add_comment(post_id, g.current_user, text)
    if not success:
        return jsonify({"error": "Post not found"}), 404
    return jsonify({"message": "Comment added"}), 201
