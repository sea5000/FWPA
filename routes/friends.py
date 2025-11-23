from flask import Blueprint, render_template, g
from utils.auth import get_current_user_from_token
from model.login_model import get_all_users
from flask import Blueprint, render_template
from routes.community import community_bp  
#from routes.community import feed_bp 

community_bp = Blueprint('community', __name__, url_prefix='/community')
feed_bp = Blueprint('feed', __name__, url_prefix='/feed')


@community_bp.route('/community/notes', endpoint='community_notes')
def community_notes():
    ...


friends_bp = Blueprint('friends', __name__)


@friends_bp.before_request
def require_auth():
    user = get_current_user_from_token()
    if not isinstance(user, str):
        return user
    g.current_user = user


@friends_bp.route('/', endpoint='index')
def friends_index():
    return render_template('friends.html', username=g.current_user, users=get_all_users())

@friends_bp.route('/community/notes', endpoint='community_notes')
def notes():
    return render_template('community.html', username=g.current_user, users=get_all_users())

@friends_bp.route('/community/feed', endpoint='feed')
def feed():
    return render_template('community_feed.html', username=g.current_user, users=get_all_users())
