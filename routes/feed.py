"""from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from datetime import datetime
from bson import ObjectId
from flask import request, jsonify
from pymongo import MongoClient
from flask import Blueprint, render_template
from routes.community import community_bp
#from routes.community import friends_bp

friends_bp = Blueprint('friends', __name__, url_prefix='/friends')
community_bp = Blueprint('community', __name__, url_prefix='/community')

@community_bp.route('/community/notes', endpoint='community_notes')
def community_notes():
    ...

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


@feed_bp.route('/community/notes', endpoint='community_notes')
def notes():
    return render_template('community.html', username=g.current_user, users=get_all_users()) 

@feed_bp.route('/community/friends', endpoint='friends')
def friends():
    return render_template('community_friends.html', username=g.current_user, users=get_all_users())




@feed_bp.route('/api/feed/posts', methods=['GET'])
def get_posts():
    # Return posts including their ids and comments, newest first
    posts = []
    for p in db.posts.find().sort('timestamp', -1):
        p['_id'] = str(p['_id'])
        posts.append(p)
    return jsonify(posts)

@feed_bp.route('/api/feed/posts/<post_id>', methods=['GET'])
def get_post(post_id):           #Returns a specific post by id
    try:
        post = db.posts.find_one({'_id': ObjectId(post_id)})
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        post['_id'] = str(post['_id'])
        return jsonify(post)
    except Exception:
        return jsonify({'error': 'Invalid post id'}), 400

@feed_bp.route('/api/feed/posts', methods=['POST'])
def create_post():                 #Creates a new post in the feed
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
def like_post(post_id):      #Likes a specific post
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
def add_comment(post_id):      #Adds a comment to a specific post
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



@feed_bp.route('/api/feed/posts/<post_id>', methods=['DELETE'])
def delete_post(post_id):   #Deletes a specific post by id
    try:
        result = db.posts.delete_one({"_id": ObjectId(post_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Post not found"}), 404
        return jsonify({"message": "Post deleted"}), 200
    except:
        return jsonify({"error": "Invalid ID"}), 400"""


from flask import Blueprint, request, jsonify, render_template, g
from pymongo import MongoClient
from datetime import datetime
from utils.auth import get_current_user_from_token
from werkzeug.utils import secure_filename
import os
from model.login_model import get_all_users

feed_bp = Blueprint("feed", __name__)
client = MongoClient("mongodb://localhost:27017/")
db = client.bookme    # Your existing database


# Authentication for every request
@feed_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user



# FEED PAGE
def feed_page():
    return render_template("community_feed.html", username=g.current_user)


# GET ALL POSTS
@feed_bp.route("/api/feed/posts", methods=["GET"])
def get_posts():
    posts = list(db.posts.find({}))
    for p in posts:
        p["_id"] = str(p["_id"])
    return jsonify(posts)


# CREATE NEW POST
@feed_bp.route("/api/feed/posts", methods=["POST"])
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



# LIKE POST
@feed_bp.route("/api/feed/posts/<post_id>/like", methods=["POST"])
def like_post(post_id):
    db.posts.update_one({"_id": post_id}, {"$inc": {"likes": 1}})
    return jsonify({"message": "Liked"}), 200


# GET SINGLE POST (with comments)
@feed_bp.route("/api/feed/posts/<post_id>", methods=["GET"])
def get_single_post(post_id):
    post = db.posts.find_one({"_id": post_id})
    if not post:
        return jsonify({"error": "Not found"}), 404

    post["_id"] = str(post["_id"])
    return jsonify(post)


# ADD COMMENT
@feed_bp.route("/api/feed/posts/<post_id>/comments", methods=["POST"])
def add_comment(post_id):
    data = request.get_json()
    comment = {
        "author": g.current_user,
        "text": data.get("text"),
        "timestamp": datetime.utcnow()
    }

    db.posts.update_one(
        {"_id": post_id},
        {"$push": {"comments": comment}}
    )

    return jsonify({"message": "Comment added"}), 201
"""
import os
from flask import current_app
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@community_bp.route('/api/community/posts/image', methods=['POST'])
def upload_post_with_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # create folder if missing
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        file.save(save_path)

        # save post in db
        db.posts.insert_one({
            "author": g.current_user,
            "image": filename,
            "views": 0,
            "likes": 0,
            "comments": []
        })

        return jsonify({"message": "Image post uploaded"}), 201

    return jsonify({"error": "Invalid file type"}), 400
    """




UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


'''# Display feed page
@feed_bp.route('/', endpoint='index')
def feed_index():
    posts = list(db.posts.find())
    for post in posts:
        post["_id"] = str(post["_id"])
    return render_template('feed.html', username=g.current_user, users=get_all_users(), posts=posts)'''

# Handle post with image + text
@feed_bp.route('/api/feed/posts/image', methods=['POST'])
def create_post_with_image():
    image = request.files.get('image')
    content = request.form.get('content', '')

    filename = None
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(UPLOAD_FOLDER, filename))

    post = {
        "author": g.current_user,
        "content": content,
        "image": filename,
        "likes": 0,
        "comments": []
    }
    db.posts.insert_one(post)
    return jsonify({"message": "Post created"}), 201

