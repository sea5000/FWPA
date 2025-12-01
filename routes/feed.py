from flask import Blueprint, request, jsonify, render_template, g
from datetime import datetime
from utils.auth import get_current_user_from_token
from model.login_model import get_user_by_username
from model.feed_post_model import (
    list_posts,
    get_post,
    create_post,
    like_post,
    add_comment,
)

feed_bp = Blueprint("feed", __name__)


# Authentication for every request
@feed_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


# FEED PAGE
@feed_bp.route("/", endpoint="index")
def feed_page():
    # Fetch the full profile data for the current user
    profile_data = get_user_by_username(g.current_user)
    # Pass the profile data to the template
    return render_template(
        "feed.html", username=g.current_user, profileData=profile_data
    )


# GET ALL POSTS
@feed_bp.route("/api/feed/posts", methods=["GET"])
def get_posts():
    posts = list_posts()
    # Enrich posts with author profile pictures
    for p in posts:
        author = p.get("author")
        if author:
            u = get_user_by_username(author)
            if u and u.get("profile_pic"):
                p["author_profile_pic"] = u["profile_pic"]
    return jsonify(posts)


# CREATE NEW POST
@feed_bp.route("/api/feed/posts", methods=["POST"])
def create_post_endpoint():
    data = request.get_json()
    text = data.get("text", "")
    image = data.get("image", None)
    post_id = create_post(g.current_user, text, image)
    return jsonify({"message": "Post created", "post_id": post_id}), 201


# LIKE POST
@feed_bp.route("/api/feed/posts/<post_id>/like", methods=["POST"])
def like_post_endpoint(post_id):
    success = like_post(post_id)
    if not success:
        return jsonify({"error": "Post not found"}), 404
    return jsonify({"message": "Liked"}), 200


# GET SINGLE POST (with comments)
@feed_bp.route("/api/feed/posts/<post_id>", methods=["GET"])
def get_single_post(post_id):
    post = get_post(post_id)
    if not post:
        return jsonify({"error": "Not found"}), 404
    # Enrich main post author
    author = post.get("author")
    if author:
        u = get_user_by_username(author)
        if u and u.get("profile_pic"):
            post["author_profile_pic"] = u["profile_pic"]
    # Enrich comments with author profile pictures
    comments = post.get("comments") or []
    for c in comments:
        ca = c.get("author")
        if ca:
            cu = get_user_by_username(ca)
            if cu and cu.get("profile_pic"):
                c["author_profile_pic"] = cu["profile_pic"]
    return jsonify(post)


# ADD COMMENT
@feed_bp.route("/api/feed/posts/<post_id>/comments", methods=["POST"])
def add_comment_endpoint(post_id):
    data = request.get_json()
    text = data.get("text", "")
    success = add_comment(post_id, g.current_user, text)
    if not success:
        return jsonify({"error": "Post not found"}), 404
    return jsonify({"message": "Comment added"}), 201
