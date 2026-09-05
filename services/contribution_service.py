from db.contributions import (
    get_contributions_admin,
    get_contributions_count,
    get_contribution_by_id,
    update_contribution_status,
    get_contribution_stats,
    get_public_contributions
)
from db.audit import log_audit_action
from services.privacy_service import project_public_contributions_list
from typing import Dict, Any, Optional, List

def get_contributions_dashboard(
    meet_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
) -> Dict[str, Any]:
    """Retrieve contribution queue with aggregate financial metrics."""
    offset = (page - 1) * per_page
    total_count = get_contributions_count(meet_id=meet_id, status=status, search=search)
    records = get_contributions_admin(
        meet_id=meet_id,
        status=status,
        search=search,
        limit=per_page,
        offset=offset
    )
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    stats = get_contribution_stats(meet_id=meet_id)

    return {
        "records": records,
        "total_count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "stats": stats
    }

def get_public_contributions_tracker(meet_id: Optional[int] = None, target_goal: float = 500000.0) -> Dict[str, Any]:
    """
    Retrieve public-safe contribution tracker dashboard data and honor roll
    with strict rule-based privacy filters applied.
    """
    raw_stats = get_contribution_stats(meet_id=meet_id)
    raw_records = get_public_contributions(meet_id=meet_id)

    # Apply 3-tier privacy engine to all records
    sanitized_contributors = project_public_contributions_list(raw_records)

    # Financial progress calculation
    verified_total = float(raw_stats.get("verified_amount", 0.0))
    submitted_total = float(raw_stats.get("total_submitted_amount", 0.0))
    
    # Progress towards goal (based on total verified/committed support)
    progress_percent = min(100.0, round((submitted_total / target_goal) * 100, 1)) if target_goal > 0 else 0.0

    # Privacy category counts
    public_count = sum(1 for c in sanitized_contributors if c["privacy_mode"] == "public")
    semi_anon_count = sum(1 for c in sanitized_contributors if c["privacy_mode"] == "semi_anonymous")
    fully_anon_count = sum(1 for c in sanitized_contributors if c["privacy_mode"] == "fully_anonymous")

    tracker_stats = {
        "total_raised": submitted_total,
        "verified_amount": verified_total,
        "pending_amount": float(raw_stats.get("pending_amount", 0.0)),
        "target_amount": target_goal,
        "progress_percent": progress_percent,
        "total_contributors": raw_stats.get("distinct_contributors", len(sanitized_contributors)),
        "total_submissions": raw_stats.get("total_submissions", len(sanitized_contributors)),
        "verified_count": raw_stats.get("verified_count", 0),
        "pending_count": raw_stats.get("pending_count", 0),
        "public_count": public_count,
        "semi_anon_count": semi_anon_count,
        "fully_anon_count": fully_anon_count
    }

    return {
        "stats": tracker_stats,
        "contributors": sanitized_contributors,
        "recent_contributors": sanitized_contributors[:6]
    }

def process_contribution_verification(
    contrib_id: int,
    action: str,
    user_id: int,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute payment verification state transition with audit trail.
    Allowed actions: 'verify', 'reject', 'review'
    """
    contribution = get_contribution_by_id(contrib_id)
    if not contribution:
        return {"success": False, "error": "Contribution record not found."}

    status_map = {
        "verify": "verified",
        "reject": "rejected",
        "review": "under_review"
    }

    if action not in status_map:
        return {"success": False, "error": f"Invalid verification action: {action}"}

    new_status = status_map[action]
    old_status = contribution["payment_status"]

    update_contribution_status(
        contrib_id=contrib_id,
        status=new_status,
        verified_by=user_id,
        notes=notes
    )

    # Record audit log
    log_audit_action(
        action=f"CONTRIBUTION_{new_status.upper()}",
        entity_type="contribution",
        entity_id=contrib_id,
        user_id=user_id,
        old_value=old_status,
        new_value=new_status
    )

    return {
        "success": True,
        "contrib_id": contrib_id,
        "old_status": old_status,
        "new_status": new_status,
        "message": f"Payment successfully marked as {new_status}."
    }

def delete_single_contribution(contrib_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Delete a single contribution record and log an audit trail entry."""
    from db.contributions import delete_contribution_by_id
    
    contrib = delete_contribution_by_id(contrib_id)
    if not contrib:
        return None

    log_audit_action(
        action="DELETE_CONTRIBUTION",
        entity_type="contribution",
        entity_id=contrib_id,
        user_id=user_id,
        old_value=f"Alumnus ID: {contrib.get('alumni_id')}, Amount: {contrib.get('amount')}, Status: {contrib.get('payment_status')}, Ref: {contrib.get('transaction_reference')}",
        new_value=f"Deleted contribution record #{contrib_id}."
    )
    return contrib

def clean_duplicate_contributions(user_id: Optional[int] = None) -> Dict[str, int]:
    """Scan and prune duplicate contribution records from database."""
    from db.contributions import deduplicate_contributions_db
    metrics = deduplicate_contributions_db()
    if metrics.get("duplicates_removed", 0) > 0:
        log_audit_action(
            action="DEDUPLICATE_CONTRIBUTIONS",
            entity_type="contribution",
            user_id=user_id,
            new_value=f"Automatically removed {metrics['duplicates_removed']} duplicate contribution entries."
        )
    return metrics

