from db.connection import execute_query
from typing import List, Dict, Any, Optional

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch user by email for authentication."""
    sql = "SELECT id, email, password_hash, full_name, role, is_active, created_at, updated_at FROM users WHERE email = %s"
    return execute_query(sql, (email.strip().lower(),), fetch_one=True)

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch user by ID."""
    sql = "SELECT id, email, full_name, role, is_active, created_at FROM users WHERE id = %s"
    return execute_query(sql, (user_id,), fetch_one=True)

def create_user(email: str, password_hash: str, full_name: str, role: str = "organizer") -> int:
    """Create a new admin/organizer user."""
    sql = "INSERT INTO users (email, password_hash, full_name, role) VALUES (%s, %s, %s, %s)"
    params = (email.strip().lower(), password_hash, full_name, role)
    return execute_query(sql, params, commit=True)

def get_all_users() -> List[Dict[str, Any]]:
    """List all authorized users."""
    sql = "SELECT id, email, full_name, role, is_active, created_at FROM users ORDER BY id ASC"
    return execute_query(sql, fetch_all=True)
