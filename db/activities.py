from db.connection import execute_query
from typing import List, Dict, Any, Optional

def get_activities_by_meet(meet_id: int) -> List[Dict[str, Any]]:
    """Fetch all organizing activities for a meet."""
    sql = """
        SELECT 
            a.id, a.meet_id, a.name, a.description, a.status,
            a.created_at, a.updated_at,
            COUNT(DISTINCT va.id) as assigned_volunteers_count
        FROM activities a
        LEFT JOIN volunteer_assignments va ON a.id = va.activity_id
        WHERE a.meet_id = %s
        GROUP BY a.id, a.meet_id, a.name, a.description, a.status, a.created_at, a.updated_at
        ORDER BY a.id ASC
    """
    return execute_query(sql, (meet_id,), fetch_all=True)

def get_activity_by_id(activity_id: int) -> Optional[Dict[str, Any]]:
    """Fetch single activity."""
    sql = "SELECT id, meet_id, name, description, status, created_at, updated_at FROM activities WHERE id = %s"
    return execute_query(sql, (activity_id,), fetch_one=True)

def create_activity(data: Dict[str, Any]) -> int:
    """Create organizing activity."""
    sql = "INSERT INTO activities (meet_id, name, description, status) VALUES (%s, %s, %s, %s)"
    params = (data["meet_id"], data["name"], data.get("description"), data.get("status", "planned"))
    return execute_query(sql, params, commit=True)

def update_activity(activity_id: int, data: Dict[str, Any]) -> bool:
    """Update activity."""
    sql = "UPDATE activities SET name = %s, description = %s, status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
    params = (data["name"], data.get("description"), data.get("status", "planned"), activity_id)
    execute_query(sql, params, commit=True)
    return True

def get_activity_assignments(activity_id: int) -> List[Dict[str, Any]]:
    """Fetch volunteers assigned to this activity."""
    sql = """
        SELECT 
            va.id as assignment_id, va.activity_id, va.volunteer_id,
            va.responsibility, va.status, va.created_at,
            v.full_name, v.email, v.phone, v.role as volunteer_role
        FROM volunteer_assignments va
        JOIN volunteers v ON va.volunteer_id = v.id
        WHERE va.activity_id = %s
        ORDER BY va.created_at ASC
    """
    return execute_query(sql, (activity_id,), fetch_all=True)

def assign_volunteer_to_activity(
    activity_id: int,
    volunteer_id: int,
    responsibility: Optional[str] = None,
    status: str = "assigned"
) -> int:
    """Assign a volunteer to an activity."""
    sql = """
        INSERT INTO volunteer_assignments (activity_id, volunteer_id, responsibility, status)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            responsibility = VALUES(responsibility),
            status = VALUES(status),
            updated_at = CURRENT_TIMESTAMP
    """
    return execute_query(sql, (activity_id, volunteer_id, responsibility, status), commit=True)

def remove_volunteer_assignment(assignment_id: int) -> bool:
    """Remove a volunteer assignment."""
    sql = "DELETE FROM volunteer_assignments WHERE id = %s"
    execute_query(sql, (assignment_id,), commit=True)
    return True
