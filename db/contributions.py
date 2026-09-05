from db.connection import execute_query, get_db_cursor
from typing import List, Dict, Any, Optional
from datetime import datetime

VALID_PAYMENT_STATUSES = ["submitted", "under_review", "verified", "rejected", "refunded"]

def get_contributions_admin(
    meet_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetch contribution records with alumni metadata for organizers."""
    conditions = ["1=1"]
    params: List[Any] = []

    if meet_id:
        conditions.append("c.meet_id = %s")
        params.append(meet_id)

    if status and status in VALID_PAYMENT_STATUSES:
        conditions.append("c.payment_status = %s")
        params.append(status)

    if search:
        conditions.append("(a.full_name LIKE %s OR c.transaction_reference LIKE %s OR a.email LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT 
            c.id, c.meet_id, c.alumni_id, c.amount, c.currency,
            c.transaction_reference, c.payment_screenshot_path, c.payment_status,
            c.submitted_at, c.paid_at, c.verified_at, c.verified_by, c.notes,
            c.created_at,
            a.full_name, a.graduation_year, a.course, a.email, a.phone, a.organization,
            COALESCE(rp.recognition_type, 'name_only') AS recognition_type,
            u.full_name AS verifier_name
        FROM contributions c
        JOIN alumni a ON c.alumni_id = a.id
        LEFT JOIN recognition_preferences rp ON (c.alumni_id = rp.alumni_id AND c.meet_id = rp.meet_id)
        LEFT JOIN users u ON c.verified_by = u.id
        WHERE {where_clause}
        ORDER BY c.submitted_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    return execute_query(sql, tuple(params), fetch_all=True)

def get_contributions_count(
    meet_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> int:
    """Get total count of contributions matching filters."""
    conditions = ["1=1"]
    params: List[Any] = []

    if meet_id:
        conditions.append("c.meet_id = %s")
        params.append(meet_id)

    if status and status in VALID_PAYMENT_STATUSES:
        conditions.append("c.payment_status = %s")
        params.append(status)

    if search:
        conditions.append("(a.full_name LIKE %s OR c.transaction_reference LIKE %s)")
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard])

    sql = f"""
        SELECT COUNT(c.id) AS count
        FROM contributions c
        JOIN alumni a ON c.alumni_id = a.id
        WHERE {' AND '.join(conditions)}
    """
    row = execute_query(sql, tuple(params), fetch_one=True)
    return row["count"] if row else 0

def get_contribution_by_id(contrib_id: int) -> Optional[Dict[str, Any]]:
    """Fetch single contribution record by ID."""
    sql = """
        SELECT 
            c.id, c.meet_id, c.alumni_id, c.amount, c.currency,
            c.transaction_reference, c.payment_screenshot_path, c.payment_status,
            c.submitted_at, c.paid_at, c.verified_at, c.verified_by, c.notes,
            c.created_at, c.updated_at,
            a.full_name, a.graduation_year, a.course, a.email, a.phone, a.organization,
            COALESCE(rp.recognition_type, 'name_only') AS recognition_type
        FROM contributions c
        JOIN alumni a ON c.alumni_id = a.id
        LEFT JOIN recognition_preferences rp ON (c.alumni_id = rp.alumni_id AND c.meet_id = rp.meet_id)
        WHERE c.id = %s
    """
    return execute_query(sql, (contrib_id,), fetch_one=True)

def get_contribution_by_reference(meet_id: int, alumni_id: int, tx_ref: str) -> Optional[Dict[str, Any]]:
    """Fetch contribution by transaction reference for duplicate check."""
    if not tx_ref:
        return None
    sql = """
        SELECT id, meet_id, alumni_id, amount, currency, transaction_reference, payment_screenshot_path, payment_status
        FROM contributions
        WHERE meet_id = %s AND alumni_id = %s AND transaction_reference = %s
        LIMIT 1
    """
    return execute_query(sql, (meet_id, alumni_id, tx_ref.strip()), fetch_one=True)

def get_existing_contribution_for_sync(
    meet_id: int,
    alumni_id: int,
    tx_ref: Optional[str] = None,
    screenshot: Optional[str] = None,
    amount: Optional[float] = None
) -> Optional[Dict[str, Any]]:
    """
    Intelligently check for duplicate contribution across transaction reference,
    drive screenshot path, or existing submission for the same alumnus and meet.
    """
    clean_ref = (tx_ref or "").strip()
    if clean_ref and clean_ref.lower() not in ("not provided", "none", "0", "-", "n/a", "null"):
        res = get_contribution_by_reference(meet_id, alumni_id, clean_ref)
        if res:
            return res

    clean_ss = (screenshot or "").strip()
    if clean_ss:
        sql = """
            SELECT id, meet_id, alumni_id, amount, currency, transaction_reference, payment_screenshot_path, payment_status
            FROM contributions
            WHERE meet_id = %s AND alumni_id = %s AND payment_screenshot_path = %s
            LIMIT 1
        """
        res = execute_query(sql, (meet_id, alumni_id, clean_ss), fetch_one=True)
        if res:
            return res

    # If neither unique ref nor unique screenshot, match existing contribution for this alumnus in the meet
    sql = """
        SELECT id, meet_id, alumni_id, amount, currency, transaction_reference, payment_screenshot_path, payment_status
        FROM contributions
        WHERE meet_id = %s AND alumni_id = %s
        ORDER BY id ASC
        LIMIT 1
    """
    return execute_query(sql, (meet_id, alumni_id), fetch_one=True)

def delete_contribution_by_id(contrib_id: int) -> Optional[Dict[str, Any]]:
    """Delete a single contribution record by ID."""
    contrib = get_contribution_by_id(contrib_id)
    if not contrib:
        return None
    sql = "DELETE FROM contributions WHERE id = %s"
    execute_query(sql, (contrib_id,), commit=True)
    return contrib

def deduplicate_contributions_db() -> Dict[str, int]:
    """
    Scan contributions and remove exact duplicate records for the same alumnus & meet,
    preserving the verified or oldest entry.
    """
    from db.connection import get_connection
    conn = get_connection()
    try:
        deleted_count = 0
        with conn.cursor() as cursor:
            # Find all alumni with > 1 contribution for the same meet
            cursor.execute("""
                SELECT meet_id, alumni_id, COUNT(*) AS cnt
                FROM contributions
                GROUP BY meet_id, alumni_id
                HAVING cnt > 1
            """)
            duplicate_groups = cursor.fetchall()

            for grp in duplicate_groups:
                m_id = grp["meet_id"]
                a_id = grp["alumni_id"]
                
                cursor.execute("""
                    SELECT id, amount, transaction_reference, payment_screenshot_path, payment_status, created_at
                    FROM contributions
                    WHERE meet_id = %s AND alumni_id = %s
                    ORDER BY 
                        CASE WHEN payment_status = 'verified' THEN 0 ELSE 1 END,
                        id ASC
                """, (m_id, a_id))
                rows = cursor.fetchall()
                
                # Check for identical duplicate rows (same amount, tx_ref, screenshot)
                seen_signatures = set()
                for r in rows:
                    sig = (
                        float(r["amount"] or 0),
                        (r["transaction_reference"] or "").strip(),
                        (r["payment_screenshot_path"] or "").strip()
                    )
                    if sig in seen_signatures:
                        # Duplicate found! Delete this duplicate record
                        cursor.execute("DELETE FROM contributions WHERE id = %s", (r["id"],))
                        deleted_count += 1
                    else:
                        seen_signatures.add(sig)

        conn.commit()
        return {"duplicates_removed": deleted_count}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def create_contribution(data: Dict[str, Any]) -> int:
    """Insert a new contribution."""
    sql = """
        INSERT INTO contributions (
            meet_id, alumni_id, amount, currency, transaction_reference,
            payment_screenshot_path, payment_status, notes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data["meet_id"],
        data["alumni_id"],
        data["amount"],
        data.get("currency", "INR"),
        data.get("transaction_reference"),
        data.get("payment_screenshot_path"),
        data.get("payment_status", "submitted"),
        data.get("notes")
    )
    return execute_query(sql, params, commit=True)

def update_contribution_status(
    contrib_id: int,
    status: str,
    verified_by: Optional[int] = None,
    notes: Optional[str] = None
) -> bool:
    """Update contribution payment verification status atomically."""
    if status not in VALID_PAYMENT_STATUSES:
        raise ValueError(f"Invalid payment status: {status}")

    now = datetime.now() if status in ("verified", "rejected", "refunded") else None

    sql = """
        UPDATE contributions SET
            payment_status = %s,
            verified_at = %s,
            verified_by = %s,
            notes = COALESCE(%s, notes),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
    """
    params = (status, now, verified_by, notes, contrib_id)
    execute_query(sql, params, commit=True)
    return True

def get_contribution_stats(meet_id: Optional[int] = None) -> Dict[str, Any]:
    """Aggregate contribution financials for the meet."""
    conditions = ["1=1"]
    params: List[Any] = []
    if meet_id:
        conditions.append("meet_id = %s")
        params.append(meet_id)

    sql = f"""
        SELECT 
            COUNT(id) AS total_submissions,
            COALESCE(SUM(amount), 0) AS total_submitted_amount,
            COALESCE(SUM(CASE WHEN payment_status = 'verified' THEN amount ELSE 0 END), 0) AS verified_amount,
            COALESCE(SUM(CASE WHEN payment_status = 'submitted' OR payment_status = 'under_review' THEN amount ELSE 0 END), 0) AS pending_amount,
            COALESCE(SUM(CASE WHEN payment_status = 'verified' THEN 1 ELSE 0 END), 0) AS verified_count,
            COALESCE(SUM(CASE WHEN payment_status IN ('submitted', 'under_review') THEN 1 ELSE 0 END), 0) AS pending_count,
            COALESCE(SUM(CASE WHEN payment_status = 'rejected' THEN 1 ELSE 0 END), 0) AS rejected_count,
            COUNT(DISTINCT alumni_id) AS distinct_contributors
        FROM contributions
        WHERE {' AND '.join(conditions)}
    """
    stats = execute_query(sql, tuple(params), fetch_one=True)
    return stats or {
        "total_submissions": 0,
        "total_submitted_amount": 0,
        "verified_amount": 0,
        "pending_amount": 0,
        "verified_count": 0,
        "pending_count": 0,
        "rejected_count": 0,
        "distinct_contributors": 0
    }

def save_recognition_preference(meet_id: int, alumni_id: int, recognition_type: str) -> bool:
    """Save or update public recognition preference."""
    sql = """
        INSERT INTO recognition_preferences (meet_id, alumni_id, recognition_type)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            recognition_type = VALUES(recognition_type),
            updated_at = CURRENT_TIMESTAMP
    """
    execute_query(sql, (meet_id, alumni_id, recognition_type), commit=True)
    return True

def get_public_contributions(meet_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch non-rejected contributions projection for the public tracker.
    Note: Raw result is passed to privacy_service for strict 3-tier filtering.
    """
    conditions = ["c.payment_status != 'rejected'"]
    params: List[Any] = []

    if meet_id:
        conditions.append("c.meet_id = %s")
        params.append(meet_id)

    sql = f"""
        SELECT 
            c.id, c.meet_id, c.alumni_id, c.amount, c.currency, c.payment_status, c.submitted_at,
            a.full_name, a.graduation_year, a.course,
            COALESCE(rp.recognition_type, 'semi_anonymous') AS recognition_type
        FROM contributions c
        JOIN alumni a ON c.alumni_id = a.id
        LEFT JOIN recognition_preferences rp ON (c.alumni_id = rp.alumni_id AND c.meet_id = rp.meet_id)
        WHERE {' AND '.join(conditions)}
        ORDER BY c.submitted_at DESC, c.amount DESC
    """
    return execute_query(sql, tuple(params), fetch_all=True)
