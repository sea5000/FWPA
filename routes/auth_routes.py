"""
Authentication routes: login and logout.
"""

from flask import render_template, request, redirect, url_for, session, Blueprint
from jwt import JWT
from jwt.jwk import OctetJWK
from datetime import datetime, timedelta
from model.login_model import verify_user
from model.login_model import delete_user_by_username
from model.login_model import update_login_streak
from utils.auth import JWT_SECRET_KEY, JWT_ALGORITHM
from model.login_model import get_all_users

#__all__ = ['auth_bp']
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login():
    """
    GET route to display the login page.
    """
    # If user already has a valid token, redirect to home
    if 'token' in session:
        try:
            _jwt = JWT()
            _key = OctetJWK(JWT_SECRET_KEY.encode())
            _jwt.decode(session['token'], _key, do_verify=True, algorithms={JWT_ALGORITHM})
            return redirect(url_for('home.index'))
        except Exception:
            session.pop('token', None)
    
    return render_template('login.html', users=get_all_users())


@auth_bp.route('/login', methods=['POST'])
def login_post():
    """
    POST route to handle login form submission.
    Validates credentials and creates JWT token if successful.
    """
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Validate that username and password were provided
    if not username or not password:
        return render_template('login.html', error='Please provide both username and password', users=get_all_users())
    
    # Verify user credentials using the model
    user = verify_user(username, password)
    
    if user:
        # Update login streak (track daily logins)
        update_login_streak(user['username'])
        
        # Create JWT token
        token_payload = {
            'username': user['username'],
            'user_id': user['id'],
            # python-jwt expects numeric `exp` (seconds since epoch)
            'exp': int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        }

        _jwt = JWT()
        _key = OctetJWK(JWT_SECRET_KEY.encode())
        token = _jwt.encode(token_payload, _key, alg=JWT_ALGORITHM)

        # Store token in session
        session['token'] = token
        session['username'] = user['username']

        # Redirect to dashboard page
        return redirect(url_for('home.index'))
    else:
        # Invalid credentials
        return render_template('login.html', error='Invalid username or password', users=get_all_users(),login=True)


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Logout route that clears the session and redirects to login.
    """
    session.pop('token', None)
    session.pop('username', None)
    return redirect(url_for('auth.login'))

@auth_bp.route('/delete_account', methods=['POST'])
def delete_account():
    """
    Delete account route that removes the user account and redirects to signup.
    """
    username = session.pop('username', None)
    session.pop('token', None)
    if username:
        delete_user_by_username(username)
    return redirect(url_for('signup.index'))
