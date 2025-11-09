from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from datetime import datetime
from bson import ObjectId
from flask import request, jsonify
from pymongo import MongoClient
feed_bp = Blueprint('feed', __name__)


@feed_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@feed_bp.route('/', endpoint='index')
def feed_index():
    return render_template('feed.html', username=g.current_user, users=get_all_users())

@feed_bp.route('/api/feed/posts', methods=['GET'])
def get_posts():
    posts = list(db.posts.find({}, {'_id': 0}))
    return jsonify(posts)

@feed_bp.route('/api/feed/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    data['author'] = g.current_user
    data['views'] = 0
    data['comments'] = []
    db.posts.insert_one(data)
    return jsonify({'message': 'Post created'}), 201


@feed_bp.route('/api/feed/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    comment = request.get_json()
    comment['author'] = g.current_user
    comment['timestamp'] = datetime.now().isoformat()
    db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$push': {'comments': comment}}
    )
    return jsonify({'message': 'Comment added'}), 200

