from flask import Blueprint, render_template, g, request, jsonify, url_for, current_app
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users, get_user_by_username, update_user_profile_pic, update_user_password
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint("profile", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


@profile_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@profile_bp.route("/", endpoint="index")
def profile_index():
    return render_template(
        "profile-settings.html",
        username=g.current_user,
        users=get_all_users(),
        profileData=get_user_by_username(g.current_user),
    )


@profile_bp.route("/upload-avatar", methods=["POST"], endpoint="upload_avatar")
def upload_avatar():
    """Handle profile avatar upload or removal.

    Expects multipart/form-data with file field named 'avatar' to upload,
    or form field 'remove'=1 to remove the existing avatar.
    """
    username = g.current_user
    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "user not found"}), 404

    # Handle removal
    if request.form.get("remove"):
        prev = user.get("profile_pic")
        if prev:
            # remove file if exists under static/profile_pics
            try:
                filename = os.path.basename(prev)
                path = os.path.join(
                    current_app.root_path, "static", "profile_pics", filename
                )
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
        # Update MongoDB to remove profile_pic
        print(f"upload_avatar: Attempting to remove profile_pic from MongoDB for user '{username}'")
        update_success = update_user_profile_pic(username, None)
        if not update_success:
            print(f"ERROR: Failed to remove profile_pic from MongoDB for user '{username}'")
        else:
            print(f"SUCCESS: Profile picture removed from MongoDB for user '{username}'")
        return jsonify({"success": True, "profile_pic": ""})

    # Handle upload
    if "avatar" not in request.files:
        return jsonify({"error": "no file provided"}), 400
    file = request.files["avatar"]
    if file.filename == "":
        return jsonify({"error": "empty filename"}), 400

    filename = secure_filename(file.filename)
    if "." not in filename:
        return jsonify({"error": "invalid filename"}), 400
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "invalid file type"}), 400

    folder = os.path.join(current_app.root_path, "static", "profile_pics")
    os.makedirs(folder, exist_ok=True)
    save_name = f"{username}.{ext}"
    save_path = os.path.join(folder, save_name)
    file.save(save_path)

    # Generate the URL for the saved file
    profile_pic_url = url_for("static", filename=f"profile_pics/{save_name}")
    
    # Update MongoDB with the new profile picture URL
    print(f"upload_avatar: Attempting to update MongoDB for user '{username}' with URL '{profile_pic_url}'")
    update_success = update_user_profile_pic(username, profile_pic_url)
    if not update_success:
        # Log the error but still return success since file was saved
        print(f"ERROR: Failed to update profile_pic in MongoDB for user '{username}'. File saved but DB not updated.")
        # Try to verify what happened
        user_after = get_user_by_username(username)
        if user_after:
            print(f"Current profile_pic in DB for '{username}': {user_after.get('profile_pic')}")
    else:
        print(f"SUCCESS: MongoDB updated for user '{username}'")

    return jsonify({"success": True, "profile_pic": profile_pic_url})


@profile_bp.route("/change-password", methods=["POST"], endpoint="change_password")
def change_password():
    """Handle password change request.
    
    Expects JSON with 'new_password' field.
    """
    username = g.current_user
    user = get_user_by_username(username)
    if not user:
        return jsonify({"error": "user not found"}), 404
    
    # Get the new password from request
    data = request.get_json()
    if not data:
        return jsonify({"error": "no data provided"}), 400
    
    new_password = data.get("new_password")
    if not new_password:
        return jsonify({"error": "new_password is required"}), 400
    
    # Update password in MongoDB
    print(f"change_password: Attempting to update password for user '{username}'")
    update_success = update_user_password(username, new_password)
    if not update_success:
        print(f"ERROR: Failed to update password in MongoDB for user '{username}'")
        return jsonify({"error": "Failed to update password"}), 500
    else:
        print(f"SUCCESS: Password updated for user '{username}'")
        return jsonify({"success": True, "message": "Password updated successfully"})
