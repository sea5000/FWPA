from flask import Blueprint, render_template, g, request, jsonify, url_for, current_app
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users, get_user_by_username
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
        user.pop("profile_pic", None)
        return jsonify({"success": True, "profile_pic": user.get("profile_pic", "")})

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

    # Update in-memory user record to point to the static url
    user["profile_pic"] = url_for("static", filename=f"profile_pics/{save_name}")

    return jsonify({"success": True, "profile_pic": user["profile_pic"]})
