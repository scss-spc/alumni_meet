from db.connection import execute_query
from typing import List, Dict, Any, Optional

def get_all_volunteers(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Fetch volunteer records.
    RULE: Completely independent of alumni table.
    """
    conditions = ["1=1"]
    params: List[Any] = []

    if status:
        conditions.append("v.status = %s")
        params.append(status)

    if search:
        conditions.append("(v.full_name LIKE %s OR v.email LIKE %s OR v.role LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT 
            v.id, v.full_name, v.email, v.phone, v.role, v.status, v.notes,
            v.created_at, v.updated_at,
            COUNT(DISTINCT va.id) as assignment_count
        FROM volunteers v
        LEFT JOIN volunteer_assignments va ON v.id = va.volunteer_id
        WHERE {where_clause}
        GROUP BY v.id, v.full_name, v.email, v.phone, v.role, v.status, v.notes, v.created_at, v.updated_at
        ORDER BY v.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    return execute_query(sql, tuple(params), fetch_all=True)

def get_volunteer_by_id(volunteer_id: int) -> Optional[Dict[str, Any]]:
    """Fetch volunteer profile by ID."""
    sql = "SELECT id, full_name, email, phone, role, status, notes, created_at, updated_at FROM volunteers WHERE id = %s"
    return execute_query(sql, (volunteer_id,), fetch_one=True)

def create_volunteer(data: Dict[str, Any]) -> int:
    """Create a new volunteer."""
    sql = """
        INSERT INTO volunteers (full_name, email, phone, role, status, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get("full_name"),
        data.get("email"),
        data.get("phone"),
        data.get("role"),
        data.get("status", "active"),
        data.get("notes")
    )
    return execute_query(sql, params, commit=True)

def update_volunteer(volunteer_id: int, data: Dict[str, Any]) -> bool:
    """Update volunteer details."""
    sql = """
        UPDATE volunteers SET
            full_name = %s,
            email = %s,
            phone = %s,
            role = %s,
            status = %s,
            notes = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    params = (
        data.get("full_name"),
        data.get("email"),
        data.get("phone"),
        data.get("role"),
        data.get("status", "active"),
        data.get("notes"),
        volunteer_id
    )
    execute_query(sql, params, commit=True)
    return True

def get_volunteer_count() -> int:
    """Count total active volunteers."""
    sql = "SELECT COUNT(*) as count FROM volunteers WHERE status = 'active'"
    row = execute_query(sql, fetch_one=True)
    return row["count"] if row else 0
