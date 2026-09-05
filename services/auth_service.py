import functools
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from db.users import get_user_by_email, get_user_by_id, create_user
from config import Config
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Generate secure password hash."""
    return generate_password_hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify plain password against stored hash."""
    return check_password_hash(password_hash, plain_password)

def authenticate_user(email: str, password: str):
    """Authenticate organizer/admin user."""
    user = get_user_by_email(email)
    if not user:
        return None
    if not user.get("is_active"):
        return None
    if verify_password(password, user["password_hash"]):
        return user
    return None

def login_user_session(user: dict):
    """Store user details in session."""
    session.clear()
    session["user_id"] = user["id"]
    session["user_email"] = user["email"]
    session["user_name"] = user["full_name"]
    session["user_role"] = user["role"]

def logout_user_session():
    """Clear user session."""
    session.clear()

def get_current_user():
    """Retrieve currently logged in user info."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user_by_id(user_id)

def ensure_seed_admin():
    """Ensure the default administrator user exists in TiDB on startup."""
    admin_email = Config.ADMIN_EMAIL
    if not admin_email:
        return
    existing = get_user_by_email(admin_email)
    if not existing:
        logger.info(f"Creating initial admin account for {admin_email}...")
        pwd_hash = hash_password(Config.ADMIN_PASSWORD)
        create_user(
            email=admin_email,
            password_hash=pwd_hash,
            full_name=Config.ADMIN_NAME,
            role="admin"
        )
        logger.info("Admin account seeded successfully.")

def login_required(view):
    """Decorator ensuring user is authenticated."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                from flask import jsonify
                return jsonify({"success": False, "error": "Authentication required."}), 401
            flash("Please sign in to access the organizer area.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        return view(**kwargs)
    return wrapped_view

def admin_required(view):
    """Decorator ensuring user has admin privileges."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access this area.", "warning")
            return redirect(url_for("admin.login", next=request.path))
        if session.get("user_role") != "admin":
            flash("You do not have administrative permissions for this action.", "danger")
            return redirect(url_for("admin.dashboard"))
        return view(**kwargs)
    return wrapped_view
