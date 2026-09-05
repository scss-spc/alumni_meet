from db.alumni import (
    get_public_alumni_list,
    get_all_alumni_admin,
    get_alumni_count,
    get_alumnus_by_id,
    get_alumnus_by_email,
    create_alumnus,
    update_alumnus,
    get_distinct_batches,
    get_distinct_courses
)
from db.meets import get_meet_response_by_alumni
from db.contributions import get_contributions_admin
from typing import List, Dict, Any, Optional

def get_public_alumni_directory(
    meet_id: Optional[int] = None,
    search: Optional[str] = None,
    graduation_year: Optional[int] = None,
    course: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Retrieve sanitized alumni list for public display according to recognition rules.
    Strictly safeguards privacy: no emails, no phones, no payment details.
    """
    raw_list = get_public_alumni_list(
        meet_id=meet_id,
        search=search,
        graduation_year=graduation_year,
        course=course,
        limit=limit,
        offset=offset
    )

    sanitized = []
    for item in raw_list:
        recog = item.get("recognition_type", "name_only")
        
        name = item.get("full_name", "")
        org = item.get("organization")
        desig = item.get("designation")
        batch = item.get("graduation_year")
        course_name = item.get("course")
        location = item.get("current_location")

        if recog == "anonymous":
            name = "SC&SS Alumnus (Anonymous)"
            org = None
            desig = None
        elif recog == "name_only":
            org = None
            desig = None
        elif recog == "name_and_batch":
            org = None
            desig = None
        # if 'name_and_organization' or 'full_recognition', org and desig remain

        sanitized.append({
            "id": item["id"],
            "full_name": name,
            "graduation_year": batch,
            "course": course_name,
            "organization": org,
            "designation": desig,
            "current_location": location,
            "recognition_type": recog
        })

    return sanitized

def get_admin_alumni_roster(
    search: Optional[str] = None,
    graduation_year: Optional[int] = None,
    course: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
) -> Dict[str, Any]:
    """Retrieve full paginated alumni list with contact and meet stats for organizers."""
    offset = (page - 1) * per_page
    total_count = get_alumni_count(search, graduation_year, course)
    records = get_all_alumni_admin(
        search=search,
        graduation_year=graduation_year,
        course=course,
        limit=per_page,
        offset=offset
    )
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    return {
        "records": records,
        "total_count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "batches": get_distinct_batches(),
        "courses": get_distinct_courses()
    }

def get_alumnus_detail_admin(alumni_id: int, meet_id: int = 1) -> Optional[Dict[str, Any]]:
    """Fetch complete alumnus profile, meet response, and contribution history."""
    alumnus = get_alumnus_by_id(alumni_id)
    if not alumnus:
        return None

    meet_response = get_meet_response_by_alumni(meet_id, alumni_id)
    contributions = get_contributions_admin(search=alumnus["email"])

    return {
        "alumnus": alumnus,
        "meet_response": meet_response,
        "contributions": contributions
    }

def purge_all_alumni_records(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Purge all alumni records, contributions, meet responses and record audit log."""
    from db.alumni import delete_all_alumni_data
    from db.audit import log_audit_action

    metrics = delete_all_alumni_data()
    log_audit_action(
        action="PURGE_ALL_ALUMNI",
        entity_type="alumni",
        user_id=user_id,
        new_value=(
            f"Purged {metrics['alumni_deleted']} alumni, "
            f"{metrics['contributions_deleted']} contributions, "
            f"{metrics['responses_deleted']} responses, "
            f"{metrics['recognition_deleted']} recognition settings."
        )
    )
    return metrics

def delete_single_alumnus(alumni_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Delete a single alumni record and its associated data, recording an audit log entry.
    """
    from db.alumni import delete_alumnus_by_id
    from db.audit import log_audit_action

    metrics = delete_alumnus_by_id(alumni_id)
    if not metrics:
        return None

    log_audit_action(
        action="DELETE_SINGLE_ALUMNUS",
        entity_type="alumni",
        entity_id=alumni_id,
        user_id=user_id,
        old_value=f"Name: {metrics['full_name']}, Email: {metrics['email']}, Batch: {metrics['graduation_year']}",
        new_value=(
            f"Deleted alumnus (ID #{alumni_id}). "
            f"Removed {metrics['responses_deleted']} responses, "
            f"{metrics['contributions_deleted']} contributions, "
            f"{metrics['recognition_deleted']} recognition settings."
        )
    )
    return metrics

