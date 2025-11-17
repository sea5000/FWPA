from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from datetime import datetime
from bson import ObjectId
from flask import request, jsonify
from pymongo import MongoClient
feed_bp = Blueprint('feed', __name__)


# MongoDB client and database (align with community routes)
client = MongoClient("mongodb://localhost:27017/")
db = client.bookme


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
    # Return posts including their ids and comments, newest first
    posts = []
    for p in db.posts.find().sort('timestamp', -1):
        p['_id'] = str(p['_id'])
        posts.append(p)
    return jsonify(posts)

@feed_bp.route('/api/feed/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    try:
        post = db.posts.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        post['_id'] = str(post['_id'])
        return jsonify(post)
    except Exception:
        return jsonify({'error': 'Invalid post id'}), 400

@feed_bp.route('/api/feed/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    data['author'] = g.current_user
    data['views'] = 0
    data['comments'] = []
    data['likes'] = 0
    data['timestamp'] = datetime.now().isoformat()
    data['image'] = data.get("image", None)
    result = db.posts.insert_one(data)
    return jsonify({'message': 'Post created', 'post_id': str(result.inserted_id)}), 201

@feed_bp.route('/api/feed/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):
    try:
        update_result = db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$inc': {'likes': 1}}
        )
        if update_result.matched_count == 0:
            return jsonify({'error': 'Post not found'}), 404
        return jsonify({'message': 'Liked'}), 200
    except Exception:
        return jsonify({'error': 'Invalid post id'}), 400

@feed_bp.route('/api/feed/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    comment = request.get_json()
    comment['author'] = g.current_user
    comment['timestamp'] = datetime.now().isoformat()
    try:
        update_result = db.posts.update_one(
            {'_id': ObjectId(post_id)},
            {'$push': {'comments': comment}}
        )
        if update_result.matched_count == 0:
            return jsonify({'error': 'Post not found'}), 404
        return jsonify({'message': 'Comment added'}), 200
    except Exception:
        return jsonify({'error': 'Invalid post id'}), 400

