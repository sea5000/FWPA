"""from bson import ObjectId
from flask import Blueprint, render_template, g
from routes.friends import notes
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
    notes = list(db.notes.find({}, {'_id': 0}))
    return render_template('community.html', username=g.current_user, users=get_all_users(), notes=notes)


comment @community_bp.route('/')
def community_page():
    notes = list(db.notes.find({}, {'_id': 0}))
    return render_template('community.html', notes=notes) comment

@community_bp.route('/friends', endpoint='friends')
def friends():
    return render_template('community_friends.html', username=g.current_user, users=get_all_users())

@community_bp.route('/feed', endpoint='feed')
def feed():
    return render_template('community_feed.html', username=g.current_user, users=get_all_users())


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


@community_bp.route('/api/notes', methods=['POST'])
def upload_note():                 #Uploads a new note to the community
    data = request.get_json()
    data['author'] = g.current_user
    data['views'] = 0
    db.notes.insert_one(data)
    return jsonify({'message': 'Note uploaded successfully'}), 201

@community_bp.route('/api/community/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):         #Adds a comment to a specific note
    comment = request.get_json()
    comment['author'] = g.current_user

    db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$push': {'comments': comment}}
    )
    return jsonify({'message': 'Comment added'}), 200

@community_bp.route('/api/community/posts/<post_id>/like', methods=['POST'])
def like_post(post_id):          #Likes a specific note
    db.posts.update_one(
        {'_id': ObjectId(post_id)},
        {'$inc': {'likes': 1}}
    )
    return jsonify({'message': 'Post liked'}), 200"""

from bson import ObjectId
from flask import Blueprint, render_template, g, request, jsonify
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from pymongo import MongoClient
from datetime import datetime

community_bp = Blueprint("community", __name__)

client = MongoClient("mongodb://localhost:27017/")
db = client.bookme


@community_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user

#shows notes
@community_bp.route("/", endpoint="index")
def community_index():
    notes = list(db.notes.find({}))
    for n in notes:
        n["_id"] = str(n["_id"])
    return render_template(
        "community.html",
        username=g.current_user,
        users=get_all_users(),
        notes=notes
    )



# COMMUNITY FRIENDS PAGE
@community_bp.route("/friends", endpoint="friends")
def friends():
    return render_template(
        "community_friends.html",
        username=g.current_user,
        users=get_all_users()
    )



# COMMUNITY FEED PAGE
@community_bp.route("/feed", endpoint="feed")
def feed():
    return render_template(
        "community_feed.html",
        username=g.current_user,
        users=get_all_users()
    )

# READ single note
@community_bp.route("/api/notes/<note_id>", methods=["GET"])
def view_note(note_id):
    try:
        note = db.notes.find_one({"_id": ObjectId(note_id)})
        if not note:
            return jsonify({"error": "Note not found"}), 404

        db.notes.update_one({"_id": ObjectId(note_id)}, {"$inc": {"views": 1}})

        note["_id"] = str(note["_id"])
        return jsonify(note)

    except:
        return jsonify({"error": "Invalid note id"}), 400

# CREATE new note
@community_bp.route("/api/notes", methods=["POST"])
def upload_note():
    data = request.get_json()

    new_note = {
        "title": data.get("title"),
        "content": data.get("content"),
        "author": g.current_user,
        "views": 0,
        "timestamp": datetime.utcnow(),
    }

    db.notes.insert_one(new_note)

    return jsonify({"message": "Note uploaded successfully"}), 201


# READ all posts
@community_bp.route("/api/community/posts", methods=["GET"])
def get_posts():
    posts = list(db.posts.find({}))
    for p in posts:
        p["_id"] = str(p["_id"])
    return jsonify(posts)


# CREATE new community post
@community_bp.route("/api/community/posts", methods=["POST"])
def create_post():
    data = request.get_json()

    new_post = {
        "author": g.current_user,
        "text": data.get("text", ""),
        "image": data.get("image", None),
        "timestamp": datetime.utcnow(),
        "likes": 0,
        "comments": []
    }

    db.posts.insert_one(new_post)
    return jsonify({"message": "Post created"}), 201


# ADD COMMENT
@community_bp.route("/api/community/posts/<post_id>/comments", methods=["POST"])
def add_comment(post_id):
    try:
        comment_data = request.get_json()

        comment = {
            "author": g.current_user,
            "text": comment_data.get("text"),
            "timestamp": datetime.utcnow()
        }

        db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$push": {"comments": comment}}
        )
        return jsonify({"message": "Comment added"}), 200

    except:
        return jsonify({"error": "Invalid post id"}), 400


# LIKE POST
@community_bp.route("/api/community/posts/<post_id>/like", methods=["POST"])
def like_post(post_id):
    try:
        db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"likes": 1}}
        )
        return jsonify({"message": "Post liked"}), 200

    except:
        return jsonify({"error": "Invalid post id"}), 400


