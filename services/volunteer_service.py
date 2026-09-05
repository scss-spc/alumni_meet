from db.volunteers import (
    get_all_volunteers,
    get_volunteer_by_id,
    create_volunteer,
    update_volunteer,
    get_volunteer_count
)
from db.activities import (
    get_activities_by_meet,
    get_activity_by_id,
    create_activity,
    update_activity,
    get_activity_assignments,
    assign_volunteer_to_activity,
    remove_volunteer_assignment
)
from typing import Dict, Any, List, Optional

def get_volunteer_roster(status: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve list of volunteers."""
    return get_all_volunteers(status=status, search=search)

def save_volunteer(data: Dict[str, Any]) -> int:
    """Create or update volunteer record."""
    vol_id = data.get("id")
    if vol_id:
        update_volunteer(int(vol_id), data)
        return int(vol_id)
    return create_volunteer(data)

def get_activities_overview(meet_id: int = 1) -> List[Dict[str, Any]]:
    """Fetch organizing activities and their assigned volunteers."""
    activities = get_activities_by_meet(meet_id)
    for act in activities:
        act["assignments"] = get_activity_assignments(act["id"])
    return activities

def add_activity(meet_id: int, name: str, description: Optional[str] = None) -> int:
    """Add new event organizing workstream."""
    return create_activity({"meet_id": meet_id, "name": name, "description": description})

def assign_volunteer(activity_id: int, volunteer_id: int, responsibility: Optional[str] = None) -> int:
    """Assign volunteer to an activity."""
    return assign_volunteer_to_activity(activity_id, volunteer_id, responsibility)

def unassign_volunteer(assignment_id: int) -> bool:
    """Unassign volunteer from an activity."""
    return remove_volunteer_assignment(assignment_id)
