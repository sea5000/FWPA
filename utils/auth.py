"""
Authentication utilities including JWT token management and decorators.
"""

from flask import request, redirect, url_for, session, jsonify
from functools import wraps
import os

# Use the installed `python-jwt` package's API (JWT class + JWK octet key)
from jwt import JWT
from jwt.jwk import OctetJWK
from jwt.exceptions import JWTDecodeError

# JWT secret key (in production, use environment variable)
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

# Prepare reusable JWT instance and symmetric key
_jwt = JWT()
_jwk_key = OctetJWK(JWT_SECRET_KEY.encode())


def token_required(f):
    """
    Decorator to protect routes that require JWT authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in session first
        if 'token' in session:
            token = session['token']
        # Also check for token in Authorization header
        elif 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return redirect(url_for('auth.login'))
        
        try:
            # Decode and verify the token using python-jwt's JWT instance and OctetJWK key
            data = _jwt.decode(token, _jwk_key, do_verify=True, algorithms={JWT_ALGORITHM})
            current_user = data.get('username')
        except JWTDecodeError:
            # Covers expired or otherwise invalid tokens
            session.pop('token', None)
            return redirect(url_for('auth.login'))
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def get_current_user_from_token():
    """
    Verify token from session or Authorization header and return the current username.
    Mirrors the logic used in the `token_required` decorator but returns the username
    (or redirects to login on failure).
    """
    token = None

    # Check for token in session first
    from flask import session, request, redirect, url_for

    if 'token' in session:
        token = session['token']
    elif 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return redirect(url_for('auth.login'))

    if not token:
        return redirect(url_for('auth.login'))

    try:
        data = _jwt.decode(token, _jwk_key, do_verify=True, algorithms={JWT_ALGORITHM})
        current_user = data.get('username')
    except JWTDecodeError:
        session.pop('token', None)
        return redirect(url_for('auth.login'))

    return current_user

