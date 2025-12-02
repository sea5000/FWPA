"""
Flask application with login functionality and JWT-protected home page.
Main application file that registers blueprints from the routes folder.
"""

from flask import Flask, redirect, url_for
import os
from routes import (
    auth_bp,
    login_bp,
    home_bp,
    study_bp,
    community_bp,
    challenges_bp,
    flashcards_bp,
    progress_bp,
    feed_bp,
    friends_bp,
    signup_bp,
    profile_bp,
    streak_bp,
    timer_bp,
    chatProxy_bp
)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Register blueprints with sensible URL prefixes per feature
# auth kept at root to preserve /login and /logout paths
app.register_blueprint(auth_bp)
app.register_blueprint(login_bp, url_prefix='/login')
app.register_blueprint(home_bp, url_prefix='/home')
app.register_blueprint(study_bp, url_prefix='/study')
app.register_blueprint(community_bp, url_prefix='/community')
app.register_blueprint(challenges_bp, url_prefix='/challenges')
app.register_blueprint(flashcards_bp, url_prefix='/flashcards')
app.register_blueprint(progress_bp, url_prefix='/progress')
app.register_blueprint(feed_bp, url_prefix='/feed')
app.register_blueprint(friends_bp, url_prefix='/friends')
app.register_blueprint(signup_bp, url_prefix='/signup')
app.register_blueprint(profile_bp, url_prefix='/profile-settings')
app.register_blueprint(streak_bp, url_prefix='/streak')
app.register_blueprint(timer_bp, url_prefix='/timer')
app.register_blueprint(chatProxy_bp, url_prefix='/api/chat-proxy')




@app.route('/')
def index():
    """ 
    Root route - redirects to login page.
    """
    return redirect(url_for('auth.login'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)