from db.connection import execute_query
from typing import List, Dict, Any, Optional

def log_audit_action(
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None
) -> int:
    """Record an audit trail event for administrative/financial mutations."""
    sql = """
        INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_value, new_value)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_query(sql, (user_id, action, entity_type, entity_id, old_value, new_value), commit=True)

def get_recent_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent audit logs."""
    sql = """
        SELECT 
            al.id, al.user_id, al.action, al.entity_type, al.entity_id,
            al.old_value, al.new_value, al.created_at,
            u.full_name as user_name, u.email as user_email
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT %s
    """
    return execute_query(sql, (limit,), fetch_all=True)
