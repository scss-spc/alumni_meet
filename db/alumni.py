from db.connection import execute_query, get_db_cursor
from typing import List, Dict, Any, Optional

def get_public_alumni_list(
    meet_id: Optional[int] = None,
    search: Optional[str] = None,
    graduation_year: Optional[int] = None,
    course: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Fetch alumni list projection strictly for public display.
    PRIVACY RULE: Never SELECT * and never expose email, phone, or payment references.
    """
    conditions = ["1=1"]
    params: List[Any] = []

    if meet_id:
        conditions.append("mr.meet_id = %s AND mr.attending = 1")
        params.append(meet_id)

    if search:
        conditions.append("(a.full_name LIKE %s OR a.organization LIKE %s OR a.designation LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    if graduation_year:
        conditions.append("a.graduation_year = %s")
        params.append(graduation_year)

    if course:
        conditions.append("a.course = %s")
        params.append(course)

    where_clause = " AND ".join(conditions)

    # Note: Only public-safe columns are projected.
    sql = f"""
        SELECT 
            a.id,
            a.full_name,
            a.graduation_year,
            a.course,
            a.organization,
            a.designation,
            a.current_location,
            COALESCE(MAX(rp.recognition_type), 'name_only') AS recognition_type
        FROM alumni a
        LEFT JOIN meet_responses mr ON a.id = mr.alumni_id
        LEFT JOIN recognition_preferences rp ON (a.id = rp.alumni_id AND (mr.meet_id IS NULL OR rp.meet_id = mr.meet_id))
        WHERE {where_clause}
        GROUP BY a.id, a.full_name, a.graduation_year, a.course, a.organization, a.designation, a.current_location
        ORDER BY a.graduation_year DESC, a.full_name ASC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    return execute_query(sql, tuple(params), fetch_all=True)

def get_all_alumni_admin(
    search: Optional[str] = None,
    graduation_year: Optional[int] = None,
    course: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetch complete alumni roster for authorized organizers/admins."""
    conditions = ["1=1"]
    params: List[Any] = []

    if search:
        conditions.append("(a.full_name LIKE %s OR a.email LIKE %s OR a.organization LIKE %s OR a.phone LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if graduation_year:
        conditions.append("a.graduation_year = %s")
        params.append(graduation_year)

    if course:
        conditions.append("a.course = %s")
        params.append(course)

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT 
            a.id,
            a.full_name,
            a.graduation_year,
            a.course,
            a.email,
            a.phone,
            a.organization,
            a.designation,
            a.current_location,
            a.created_at,
            a.updated_at,
            COUNT(DISTINCT mr.id) as response_count,
            COUNT(DISTINCT c.id) as contribution_count,
            COALESCE(SUM(CASE WHEN c.payment_status = 'verified' THEN c.amount ELSE 0 END), 0) as total_verified_contribution
        FROM alumni a
        LEFT JOIN meet_responses mr ON a.id = mr.alumni_id
        LEFT JOIN contributions c ON a.id = c.alumni_id
        WHERE {where_clause}
        GROUP BY a.id, a.full_name, a.graduation_year, a.course, a.email, a.phone, a.organization, a.designation, a.current_location, a.created_at, a.updated_at
        ORDER BY a.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    return execute_query(sql, tuple(params), fetch_all=True)

def get_alumni_count(search: Optional[str] = None, graduation_year: Optional[int] = None, course: Optional[str] = None) -> int:
    """Get total count of alumni matching criteria."""
    conditions = ["1=1"]
    params: List[Any] = []

    if search:
        conditions.append("(full_name LIKE %s OR email LIKE %s OR organization LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    if graduation_year:
        conditions.append("graduation_year = %s")
        params.append(graduation_year)

    if course:
        conditions.append("course = %s")
        params.append(course)

    sql = f"SELECT COUNT(*) as count FROM alumni WHERE {' AND '.join(conditions)}"
    row = execute_query(sql, tuple(params), fetch_one=True)
    return row["count"] if row else 0

def get_alumnus_by_id(alumni_id: int) -> Optional[Dict[str, Any]]:
    """Fetch complete alumnus profile by ID."""
    sql = """
        SELECT 
            id, full_name, graduation_year, course, email, phone,
            organization, designation, current_location, created_at, updated_at
        FROM alumni
        WHERE id = %s
    """
    return execute_query(sql, (alumni_id,), fetch_one=True)

def get_alumnus_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Fetch alumnus by email address."""
    sql = """
        SELECT 
            id, full_name, graduation_year, course, email, phone,
            organization, designation, current_location, created_at, updated_at
        FROM alumni
        WHERE email = %s
    """
    return execute_query(sql, (email.strip().lower(),), fetch_one=True)

def create_alumnus(data: Dict[str, Any]) -> int:
    """Insert a new alumnus record using parameterized SQL."""
    sql = """
        INSERT INTO alumni (
            full_name, graduation_year, course, email, phone,
            organization, designation, current_location
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get("full_name"),
        data.get("graduation_year"),
        data.get("course"),
        data.get("email", "").strip().lower(),
        data.get("phone"),
        data.get("organization"),
        data.get("designation"),
        data.get("current_location")
    )
    return execute_query(sql, params, commit=True)

def update_alumnus(alumni_id: int, data: Dict[str, Any]) -> bool:
    """Update an existing alumnus profile."""
    sql = """
        UPDATE alumni SET
            full_name = %s,
            graduation_year = %s,
            course = %s,
            phone = %s,
            organization = %s,
            designation = %s,
            current_location = %s
        WHERE id = %s
    """
    params = (
        data.get("full_name"),
        data.get("graduation_year"),
        data.get("course"),
        data.get("phone"),
        data.get("organization"),
        data.get("designation"),
        data.get("current_location"),
        alumni_id
    )
    execute_query(sql, params, commit=True)
    return True

def get_distinct_batches() -> List[int]:
    """Get list of distinct graduation years for filters."""
    sql = "SELECT DISTINCT graduation_year FROM alumni WHERE graduation_year IS NOT NULL ORDER BY graduation_year ASC"
    rows = execute_query(sql, fetch_all=True)
    return [r["graduation_year"] for r in rows] if rows else []

def get_distinct_courses() -> List[str]:
    """Get list of distinct courses for filters."""
    sql = "SELECT DISTINCT course FROM alumni WHERE course IS NOT NULL AND course != '' ORDER BY course ASC"
    rows = execute_query(sql, fetch_all=True)
    return [r["course"] for r in rows] if rows else []

def delete_all_alumni_data() -> Dict[str, int]:
    """
    Transactionally purge all alumni records, associated meet responses,
    recognition preferences, and contributions.
    Returns metrics of deleted rows.
    """
    from db.connection import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS cnt FROM alumni")
            alumni_cnt = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) AS cnt FROM contributions")
            contrib_cnt = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) AS cnt FROM meet_responses")
            resp_cnt = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) AS cnt FROM recognition_preferences")
            recog_cnt = cursor.fetchone()["cnt"]

            # Delete in strict foreign-key dependency order
            cursor.execute("DELETE FROM contributions")
            cursor.execute("DELETE FROM recognition_preferences")
            cursor.execute("DELETE FROM meet_responses")
            cursor.execute("DELETE FROM alumni")

        conn.commit()
        return {
            "alumni_deleted": alumni_cnt,
            "contributions_deleted": contrib_cnt,
            "responses_deleted": resp_cnt,
            "recognition_deleted": recog_cnt
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_alumnus_by_id(alumni_id: int) -> Optional[Dict[str, Any]]:
    """
    Transactionally delete a single alumni record and its associated
    meet responses, recognition preferences, and contributions.
    Returns details of deleted items or None if alumnus does not exist.
    """
    from db.connection import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, full_name, email, graduation_year, course FROM alumni WHERE id = %s", (alumni_id,))
            alumnus = cursor.fetchone()
            if not alumnus:
                return None

            cursor.execute("SELECT COUNT(*) AS cnt FROM contributions WHERE alumni_id = %s", (alumni_id,))
            contrib_cnt = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) AS cnt FROM meet_responses WHERE alumni_id = %s", (alumni_id,))
            resp_cnt = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) AS cnt FROM recognition_preferences WHERE alumni_id = %s", (alumni_id,))
            recog_cnt = cursor.fetchone()["cnt"]

            # Delete in strict foreign-key dependency order
            cursor.execute("DELETE FROM contributions WHERE alumni_id = %s", (alumni_id,))
            cursor.execute("DELETE FROM recognition_preferences WHERE alumni_id = %s", (alumni_id,))
            cursor.execute("DELETE FROM meet_responses WHERE alumni_id = %s", (alumni_id,))
            cursor.execute("DELETE FROM alumni WHERE id = %s", (alumni_id,))

        conn.commit()
        return {
            "alumni_id": alumni_id,
            "full_name": alumnus["full_name"],
            "email": alumnus["email"],
            "graduation_year": alumnus["graduation_year"],
            "course": alumnus["course"],
            "contributions_deleted": contrib_cnt,
            "responses_deleted": resp_cnt,
            "recognition_deleted": recog_cnt
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

