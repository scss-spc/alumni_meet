from db.meets import (
    get_meet_by_id,
    get_active_meet,
    get_all_meets,
    get_meet_stats,
    get_meet_responses_admin,
    save_meet_response
)
from typing import Dict, Any, Optional

def get_current_meet_context() -> Dict[str, Any]:
    """Retrieve active meet details along with aggregate participation metrics."""
    meet = get_active_meet()
    if not meet:
        meet = {
            "id": 1,
            "name": "SC&SS JNU Alumni Meet 2026",
            "description": "School of Computer and Systems Sciences Alumni Meet 2026",
            "event_date": None,
            "venue": "SC&SS Auditorium, JNU, New Delhi",
            "status": "registration_open"
        }
        stats = {"total_responses": 0, "total_attending_alumni": 0, "total_headcount": 0, "total_guests": 0}
    else:
        stats = get_meet_stats(meet["id"])

    return {
        "meet": meet,
        "stats": stats
    }
