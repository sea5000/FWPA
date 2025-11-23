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
from werkzeug.utils import secure_filename
import os

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

# UPDATE existing note
@community_bp.route("/api/notes/<note_id>", methods=["PUT"])
def update_note(note_id):
    data = request.get_json()
    update_fields = {
        "title": data.get("title"),
        "content": data.get("content"),
        "timestamp": datetime.utcnow()
    }
    result = db.notes.update_one({"_id": ObjectId(note_id)}, {"$set": update_fields})
    if result.matched_count == 0:
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"message": "Note updated"}), 200

# DELETE note
@community_bp.route("/api/notes/<note_id>", methods=["DELETE"])
def delete_note(note_id):
    result = db.notes.delete_one({"_id": ObjectId(note_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"message": "Note deleted"}), 200

# CREATE new note with file upload
@community_bp.route("/api/notes/upload", methods=["POST"])
def upload_note_with_file():
    title = request.form.get("title")
    content = request.form.get("content")
    file = request.files.get("file")

    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join("static/uploads", filename))

    new_note = {
        "title": title,
        "content": content,
        "author": g.current_user,
        "file": filename,
        "views": 0,
        "timestamp": datetime.utcnow()
    }

    db.notes.insert_one(new_note)
    return jsonify({"message": "Note with file uploaded"}), 201


UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#
@community_bp.route("/api/files", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected for uploading"}), 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    new_file = {
        "filename": filename,
        "author": g.current_user,
        "timestamp": datetime.utcnow()
    }

    db.files.insert_one(new_file)
    return jsonify({"message": "File uploaded successfully"}), 201

# READ all files
@community_bp.route("/api/files", methods=["GET"])
def get_files():
    files = list(db.files.find({}))
    for f in files:
        f["_id"] = str(f["_id"])
    return jsonify(files)

# DELETE file
@community_bp.route("/api/files/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    result = db.files.delete_one({"_id": ObjectId(file_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"message": "File deleted"}), 200


notes = [
    {"name": "Derivatives Rules",
     "folder": "Mathematics",
     "owner": g.current_user },
    {"name": "World War II Summary",
     "folder": "History",
    "owner": g.current_user },
    {"name": "Cell Division Overview",
     "folder": "Biology",
     "owner": "Alice Chen" }

]