from db.contributions import (
    get_contributions_admin,
    get_contributions_count,
    get_contribution_stats,
    get_public_contributions
)
from db.audit import log_audit_action
from services.privacy_service import project_public_contributions_list
from typing import Dict, Any, Optional, List

def get_contributions_dashboard(
    meet_id: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
) -> Dict[str, Any]:
    """Retrieve contribution queue with aggregate financial metrics."""
    offset = (page - 1) * per_page
    total_count = get_contributions_count(meet_id=meet_id, search=search)
    records = get_contributions_admin(
        meet_id=meet_id,
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
    submitted_total = float(raw_stats.get("total_submitted_amount", 0.0))
    
    # Progress towards goal (based on total committed support)
    progress_percent = min(100.0, round((submitted_total / target_goal) * 100, 1)) if target_goal > 0 else 0.0

    # Privacy category counts
    public_count = sum(1 for c in sanitized_contributors if c["privacy_mode"] == "public")
    semi_anon_count = sum(1 for c in sanitized_contributors if c["privacy_mode"] == "semi_anonymous")
    fully_anon_count = sum(1 for c in sanitized_contributors if c["privacy_mode"] == "fully_anonymous")

    tracker_stats = {
        "total_raised": submitted_total,
        "target_amount": target_goal,
        "progress_percent": progress_percent,
        "total_contributors": raw_stats.get("distinct_contributors", len(sanitized_contributors)),
        "total_submissions": raw_stats.get("total_submissions", len(sanitized_contributors)),
        "public_count": public_count,
        "semi_anon_count": semi_anon_count,
        "fully_anon_count": fully_anon_count
    }

    return {
        "stats": tracker_stats,
        "contributors": sanitized_contributors,
        "recent_contributors": sanitized_contributors[:6]
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
        old_value=f"Alumnus ID: {contrib.get('alumni_id')}, Amount: {contrib.get('amount')}, Ref: {contrib.get('transaction_reference')}",
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

