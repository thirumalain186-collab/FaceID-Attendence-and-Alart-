"""
Authentication Module for Smart Attendance System v2
Simple session-based authentication
"""

import secrets
import hashlib
from functools import wraps
from flask import session, request, jsonify
import database
from logger import get_logger

logger = get_logger()

# Default users (in production, use database or environment variables)
_DEFAULT_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "name": "Administrator"
    },
    "viewer": {
        "password_hash": hashlib.sha256("viewer123".encode()).hexdigest(),
        "role": "viewer", 
        "name": "Viewer Account"
    }
}

# Load users from database settings if configured
def _get_users():
    """Get users from database or defaults."""
    users = dict(_DEFAULT_USERS)
    
    # Check if custom admin is set (only if not empty/default)
    custom_admin = database.get_setting("admin_user")
    custom_pass = database.get_setting("admin_password")
    
    # Only override if both are set and not default-like values
    if custom_admin and custom_pass and len(custom_pass) >= 6:
        users["admin"] = {
            "password_hash": hashlib.sha256(custom_pass.encode()).hexdigest(),
            "role": "admin",
            "name": "Administrator"
        }
    
    return users


def _hash_password(password):
    """Hash password with SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            if request.is_json:
                return jsonify({"error": "Authentication required", "code": "AUTH_REQUIRED"}), 401
            return jsonify({"error": "Please login first"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({"error": "Admin access required", "code": "ADMIN_REQUIRED"}), 403
        return f(*args, **kwargs)
    return decorated


def generate_session_token():
    """Generate a secure session token."""
    return secrets.token_hex(32)


def verify_password(password, password_hash):
    """Verify password against hash."""
    return _hash_password(password) == password_hash


def authenticate(username, password):
    """Authenticate user. Returns user dict or None."""
    users = _get_users()
    
    user = users.get(username)
    if not user:
        return None
    
    if verify_password(password, user['password_hash']):
        return {
            "username": username,
            "role": user['role'],
            "name": user['name']
        }
    
    return None


def change_password(username, old_password, new_password):
    """Change user password. Returns True on success."""
    users = _get_users()
    
    user = users.get(username)
    if not user:
        return False
    
    if not verify_password(old_password, user['password_hash']):
        return False
    
    # Save to database
    if username == "admin":
        database.set_setting("admin_user", username)
        database.set_setting("admin_password", new_password)
        logger.info(f"Password changed for user: {username}")
        return True
    
    return False


def is_authenticated():
    """Check if current session is authenticated."""
    return 'user' in session


def get_current_user():
    """Get current authenticated user."""
    if 'user' not in session:
        return None
    return {
        "username": session.get('user'),
        "role": session.get('role'),
        "name": session.get('name')
    }


if __name__ == "__main__":
    # Test authentication
    result = authenticate("admin", "admin123")
    print(f"Login test: {result}")
