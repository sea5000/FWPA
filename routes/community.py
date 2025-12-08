"""Community Routes - Notes and file sharing endpoints.

This module provides Flask routes for community features:
- GET /community/: Display community notes page
- POST/GET/PUT/DELETE /api/notes: CRUD operations for notes
- POST/GET/DELETE /api/files: File upload and management
- POST /api/notes/upload: Upload note with file attachment

All routes require JWT authentication.
Notes can be organized by subject/topic for better organization.
"""

from bson import ObjectId
from flask import Blueprint, render_template, g, request, jsonify
from utils.auth import get_current_user_from_token  # JWT authentication
from model.login_model import get_all_users  # Get user list for template
from model.notes_model import upload_note as upload_note_model, view_note as view_note_model
from model.mongo import get_db  # Direct database access for complex operations
from datetime import datetime
from werkzeug.utils import secure_filename  # Sanitize filenames for security
import os

community_bp = Blueprint("community", __name__)

# Define upload directory and create if it doesn't exist
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ============================================================================
# AUTHENTICATION MIDDLEWARE
# ============================================================================

@community_bp.before_request
def require_auth():
    """Before-request hook: Verify JWT token for all community routes.
    
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

# COMMUNITY INDEX PAGE - Shows all notes
@community_bp.route("/", endpoint="index")
def community_index():
    """Display the community page with all notes.
    
    GET /community/
    
    Fetches all notes from database and converts ObjectIds to strings.
    Passes username, user list, and notes to template for rendering.
    """
    db = get_db()
    # Retrieve all notes from the notes collection
    notes = list(db.notes.find({}))
    # Convert MongoDB ObjectIds to strings for JSON/template compatibility
    for n in notes:
        n["_id"] = str(n["_id"])
    # Render template with community data
    return render_template(
        "community.html",
        username=g.current_user,
        users=get_all_users(),  # Get all users for potential collaboration features
        notes=notes  # Pass all notes to be displayed
    )


# ============================================================================
# API ROUTES - NOTE CRUD OPERATIONS
# ============================================================================

# READ single note
@community_bp.route("/api/notes/<note_id>", methods=["GET"])
def view_note_endpoint(note_id):
    """Fetch a single note by ID and increment its view count.
    
    GET /api/notes/{note_id}
    
    Returns:
        JSON note object with all fields
        404 if note not found
        
    Side effect: Increments the 'views' counter each time note is accessed.
    """
    db = get_db()
    try:
        # Convert string ID to MongoDB ObjectId for database query
        note = db.notes.find_one({"_id": ObjectId(note_id)})
        if not note:
            return jsonify({"error": "Note not found"}), 404

        # Increment view counter using MongoDB $inc operator
        # This is atomic and thread-safe
        db.notes.update_one({"_id": ObjectId(note_id)}, {"$inc": {"views": 1}})

        # Convert ObjectId to string before returning JSON
        note["_id"] = str(note["_id"])
        return jsonify(note)

    except:
        # Invalid ObjectId format
        return jsonify({"error": "Invalid note id"}), 400


# CREATE new note
@community_bp.route("/api/notes", methods=["POST"])
def upload_note_endpoint():
    """Create a new note in the community.
    
    POST /api/notes
    
    Expected JSON body:
    {
        "title": "Note Title",
        "content": "Note content text",
        "subject": "Math" (optional)
    }
    
    Returns:
        201 Created with note_id in response
    """
    data = request.get_json()
    # Prepare note data structure
    note_data = {
        "title": data.get("title"),
        "content": data.get("content"),
        "timestamp": datetime.utcnow(),  # Record when note was created
    }
    # Call model function to insert into database
    note_id = upload_note_model(g.current_user, note_data)
    return jsonify({"message": "Note uploaded successfully", "note_id": note_id}), 201


# UPDATE existing note
@community_bp.route("/api/notes/<note_id>", methods=["PUT"])
def update_note(note_id):
    """Update an existing note.
    
    PUT /api/notes/{note_id}
    
    Expected JSON body:
    {
        "title": "Updated Title",
        "content": "Updated content"
    }
    
    Returns:
        200 OK with success message
        404 if note not found
    """
    db = get_db()
    data = request.get_json()
    # Prepare update fields
    update_fields = {
        "title": data.get("title"),
        "content": data.get("content"),
        "timestamp": datetime.utcnow()  # Update modified timestamp
    }
    # Use MongoDB $set operator to update specified fields
    result = db.notes.update_one({"_id": ObjectId(note_id)}, {"$set": update_fields})
    if result.matched_count == 0:
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"message": "Note updated"}), 200


# DELETE note
@community_bp.route("/api/notes/<note_id>", methods=["DELETE"])
def delete_note(note_id):
    """Delete a note from the community.
    
    DELETE /api/notes/{note_id}
    
    Returns:
        200 OK with success message
        404 if note not found
    """
    db = get_db()
    # Remove note document from collection
    result = db.notes.delete_one({"_id": ObjectId(note_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Note not found"}), 404
    return jsonify({"message": "Note deleted"}), 200


# CREATE new note with file upload
@community_bp.route("/api/notes/upload", methods=["POST"])
def upload_note_with_file():
    """Create a note with an attached file (deprecated - use separate file endpoint).
    
    POST /api/notes/upload (multipart/form-data)
    
    Form fields:
        title: Note title
        content: Note content
        file: File to attach (optional)
    
    Returns:
        201 Created with success message
    """
    db = get_db()
    # Get form data (not JSON, since file upload uses form data)
    title = request.form.get("title")
    content = request.form.get("content")
    file = request.files.get("file")

    filename = None
    if file:
        # Sanitize filename to prevent directory traversal attacks
        filename = secure_filename(file.filename)
        # Save file to uploads directory
        file.save(os.path.join("static/uploads", filename))

    # Create note document
    new_note = {
        "title": title,
        "content": content,
        "author": g.current_user,
        "file": filename,  # Reference to uploaded file
        "views": 0,
        "timestamp": datetime.utcnow()
    }

    db.notes.insert_one(new_note)
    return jsonify({"message": "Note with file uploaded"}), 201


# ============================================================================
# API ROUTES - FILE OPERATIONS
# ============================================================================

# UPLOAD file to community
@community_bp.route("/api/files", methods=["POST"])
def upload_file():
    """Upload a standalone file to the community (not attached to a note).
    
    POST /api/files (multipart/form-data)
    
    Form fields:
        file: The file to upload
    
    Returns:
        201 Created with success message
        400 if no file provided or file empty
    """
    db = get_db()
    # Check if file was included in request
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected for uploading"}), 400
    
    # Sanitize filename for security (prevents ../../../etc/passwd attacks)
    filename = secure_filename(file.filename)
    # Save file to uploads directory
    file.save(os.path.join(UPLOAD_FOLDER, filename))

    # Create file metadata record in database
    new_file = {
        "filename": filename,
        "author": g.current_user,  # Track who uploaded
        "timestamp": datetime.utcnow()  # Track when uploaded
    }

    db.files.insert_one(new_file)
    return jsonify({"message": "File uploaded successfully"}), 201


# READ all files
@community_bp.route("/api/files", methods=["GET"])
def get_files():
    """Retrieve all uploaded files from the community.
    
    GET /api/files
    
    Returns:
        JSON array of file objects with metadata
    """
    db = get_db()
    # Retrieve all file records
    files = list(db.files.find({}))
    # Convert ObjectIds to strings for JSON
    for f in files:
        f["_id"] = str(f["_id"])
    return jsonify(files)


# DELETE file
@community_bp.route("/api/files/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    """Delete a file record from the community.
    
    DELETE /api/files/{file_id}
    
    Returns:
        200 OK with success message
        404 if file not found
        
    Note: This only removes the database record. The actual file on disk
    is not deleted (would need additional permission checks).
    """
    db = get_db()
    try:
        result = db.files.delete_one({"_id": ObjectId(file_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "File not found"}), 404
        return jsonify({"message": "File deleted"}), 200
    except:
        return jsonify({"error": "Invalid file id"}), 400
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