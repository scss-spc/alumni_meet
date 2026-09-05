from db.connection import execute_query
from typing import List, Dict, Any, Optional

def get_meet_by_id(meet_id: int) -> Optional[Dict[str, Any]]:
    """Fetch meet details by ID."""
    sql = "SELECT id, name, description, event_date, venue, status, created_at, updated_at FROM meets WHERE id = %s"
    return execute_query(sql, (meet_id,), fetch_one=True)

def get_active_meet() -> Optional[Dict[str, Any]]:
    """Fetch currently active meet or default to Meet 1."""
    sql = "SELECT id, name, description, event_date, venue, status, created_at, updated_at FROM meets WHERE status IN ('planning', 'registration_open') ORDER BY id ASC LIMIT 1"
    meet = execute_query(sql, fetch_one=True)
    if not meet:
        meet = get_meet_by_id(1)
    return meet

def get_all_meets() -> List[Dict[str, Any]]:
    """Fetch all meets."""
    sql = "SELECT id, name, description, event_date, venue, status, created_at, updated_at FROM meets ORDER BY event_date DESC, id DESC"
    return execute_query(sql, fetch_all=True)

def get_meet_response_by_alumni(meet_id: int, alumni_id: int) -> Optional[Dict[str, Any]]:
    """Fetch response of an alumnus for a specific meet."""
    sql = """
        SELECT id, meet_id, alumni_id, attending, guest_count, total_attendees,
               dietary_preferences, suggestions, submitted_at, updated_at
        FROM meet_responses
        WHERE meet_id = %s AND alumni_id = %s
    """
    return execute_query(sql, (meet_id, alumni_id), fetch_one=True)

def save_meet_response(data: Dict[str, Any]) -> int:
    """Insert or update a meet response."""
    sql = """
        INSERT INTO meet_responses (
            meet_id, alumni_id, attending, guest_count, total_attendees,
            dietary_preferences, suggestions
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            attending = VALUES(attending),
            guest_count = VALUES(guest_count),
            total_attendees = VALUES(total_attendees),
            dietary_preferences = VALUES(dietary_preferences),
            suggestions = VALUES(suggestions),
            updated_at = CURRENT_TIMESTAMP
    """
    params = (
        data["meet_id"],
        data["alumni_id"],
        1 if data.get("attending", True) else 0,
        data.get("guest_count", 0),
        data.get("total_attendees", 1),
        data.get("dietary_preferences"),
        data.get("suggestions")
    )
    return execute_query(sql, params, commit=True)

def get_meet_stats(meet_id: int) -> Dict[str, Any]:
    """Calculate aggregated stats for a meet."""
    sql = """
        SELECT 
            COUNT(id) AS total_responses,
            COALESCE(SUM(CASE WHEN attending = 1 THEN 1 ELSE 0 END), 0) AS total_attending_alumni,
            COALESCE(SUM(CASE WHEN attending = 1 THEN total_attendees ELSE 0 END), 0) AS total_headcount,
            COALESCE(SUM(CASE WHEN attending = 1 THEN guest_count ELSE 0 END), 0) AS total_guests
        FROM meet_responses
        WHERE meet_id = %s
    """
    stats = execute_query(sql, (meet_id,), fetch_one=True)
    return stats or {
        "total_responses": 0,
        "total_attending_alumni": 0,
        "total_headcount": 0,
        "total_guests": 0
    }

def get_meet_responses_admin(meet_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Fetch responses with alumnus details for admin display."""
    sql = """
        SELECT 
            mr.id, mr.meet_id, mr.alumni_id, mr.attending, mr.guest_count,
            mr.total_attendees, mr.dietary_preferences, mr.suggestions, mr.submitted_at,
            a.full_name, a.graduation_year, a.course, a.email, a.phone, a.organization
        FROM meet_responses mr
        JOIN alumni a ON mr.alumni_id = a.id
        WHERE mr.meet_id = %s
        ORDER BY mr.submitted_at DESC
        LIMIT %s OFFSET %s
    """
    return execute_query(sql, (meet_id, limit, offset), fetch_all=True)
