from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from flask import request, jsonify
from pymongo import MongoClient


community_bp = Blueprint('community', __name__)
client = MongoClient("mongodb://localhost:27017/")
db = client.bookme


@community_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@community_bp.route('/', endpoint='index')
def community_index():
    return render_template('community.html', username=g.current_user, users=get_all_users())


@community_bp.route('/community')
def community_page():
    notes = list(db.notes.find({}, {'_id': 0}))
    return render_template('community.html', notes=notes)


@community_bp.route('/api/notes/<title>', methods=['GET'])
def view_note(title):                                               #Returns full content of that note
    note = db.notes.find_one({'title': title})
    if note:
        db.notes.update_one({'title': title}, {'$inc': {'views': 1}})
        note['_id'] = str(note['_id'])
        return jsonify(note)
    return jsonify({'error': 'Note not found'}), 404


@community_bp.route('/api/community/posts', methods=['GET'])
def get_posts():                     #Returns all posts in the community    
    posts = list(db.posts.find({}, {'_id': 0}))
    return jsonify(posts)

@community_bp.route('/api/community/posts', methods=['POST'])
def create_post():                   #Creates a new post in the community
    data = request.get_json()
    data['author'] = g.current_user
    data['views'] = 0
    db.posts.insert_one(data)
    return jsonify({'message': 'Post created'}), 201

@community_bp.route('/api/notes', methods=['POST'])
def upload_note():                 #Uploads a new note to the community
    data = request.get_json()
    data['author'] = g.current_user
    data['views'] = 0
    db.notes.insert_one(data)
    return jsonify({'message': 'Note uploaded successfully'}), 201

