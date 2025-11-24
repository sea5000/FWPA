from bson import ObjectId
from flask import Blueprint, render_template, g, request, jsonify
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from model.notes_model import upload_note as upload_note_model, view_note as view_note_model
from model.mongo import get_db
from datetime import datetime
from werkzeug.utils import secure_filename
import os

community_bp = Blueprint("community", __name__)


@community_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user

#shows notes
@community_bp.route("/", endpoint="index")
def community_index():
    db = get_db()
    notes = list(db.notes.find({}))
    for n in notes:
        n["_id"] = str(n["_id"])
    return render_template(
        "community.html",
        username=g.current_user,
        users=get_all_users(),
        notes=notes
    )

# READ single note
@community_bp.route("/api/notes/<note_id>", methods=["GET"])
def view_note_endpoint(note_id):
    db = get_db()
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
def upload_note_endpoint():
    data = request.get_json()
    note_data = {
        "title": data.get("title"),
        "content": data.get("content"),
        "timestamp": datetime.utcnow(),
    }
    note_id = upload_note_model(g.current_user, note_data)
    return jsonify({"message": "Note uploaded successfully", "note_id": note_id}), 201

# UPDATE existing note
@community_bp.route("/api/notes/<note_id>", methods=["PUT"])
def update_note(note_id):
    db = get_db()
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
    db = get_db()
    result = db.notes.delete_one({"_id": ObjectId(note_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"message": "Note deleted"}), 200

# CREATE new note with file upload
@community_bp.route("/api/notes/upload", methods=["POST"])
def upload_note_with_file():
    db = get_db()
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
    db = get_db()
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
    db = get_db()
    files = list(db.files.find({}))
    for f in files:
        f["_id"] = str(f["_id"])
    return jsonify(files)

# DELETE file
@community_bp.route("/api/files/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    db = get_db()
    result = db.files.delete_one({"_id": ObjectId(file_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"message": "File deleted"}), 200

"""
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

]"""