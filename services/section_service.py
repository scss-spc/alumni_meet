import logging
from typing import List, Dict, Any, Optional
from db.sections import (
    init_site_sections_table,
    get_all_sections,
    get_sections_dict,
    get_section_by_id,
    update_section,
    reset_section_to_default
)
from db.audit import log_audit_action

logger = logging.getLogger(__name__)

def ensure_sections_initialized():
    """Ensure site_sections table is created and seeded with default sections."""
    try:
        init_site_sections_table()
    except Exception as e:
        logger.warning(f"Could not initialize site_sections table on startup: {e}")

def get_sections_for_admin(selected_page: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch sections for admin interface.
    Attaches computed fields:
    - is_customized: True if content_value is present and different from default_value.
    - current_value: content_value if non-empty else default_value.
    """
    sections = get_all_sections(page=selected_page)
    for s in sections:
        val = s.get("content_value")
        s["is_customized"] = bool(val and val.strip() != "" and val != s.get("default_value"))
        s["current_value"] = val if (val is not None and val.strip() != "") else (s.get("default_value") or "")
    return sections

def update_single_section(section_id: int, content_value: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Update a single website section and write audit log."""
    sec = get_section_by_id(section_id)
    if not sec:
        return {"success": False, "error": f"Section ID #{section_id} not found."}

    old_val = sec.get("content_value") or sec.get("default_value") or ""
    new_val = content_value.strip() if content_value is not None else ""

    update_section(section_id=section_id, content_value=new_val, updated_by=user_id)

    log_audit_action(
        user_id=user_id,
        action="update_site_section",
        entity_type="site_section",
        entity_id=section_id,
        old_value=old_val,
        new_value=new_val
    )

    return {"success": True, "section": sec}

def reset_single_section(section_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Reset a website section to its default text."""
    sec = get_section_by_id(section_id)
    if not sec:
        return {"success": False, "error": f"Section ID #{section_id} not found."}

    old_val = sec.get("content_value") or ""
    reset_section_to_default(section_id=section_id, updated_by=user_id)

    log_audit_action(
        user_id=user_id,
        action="reset_site_section",
        entity_type="site_section",
        entity_id=section_id,
        old_value=old_val,
        new_value=sec.get("default_value")
    )

    return {"success": True, "section": sec}

def bulk_update_sections(section_dict: Dict[int, str], user_id: Optional[int] = None) -> int:
    """Bulk update multiple section values."""
    updated_count = 0
    for sec_id_raw, new_val in section_dict.items():
        try:
            sec_id = int(sec_id_raw)
            res = update_single_section(section_id=sec_id, content_value=new_val, user_id=user_id)
            if res.get("success"):
                updated_count += 1
        except Exception as e:
            logger.error(f"Failed to update section ID {sec_id_raw}: {e}")
    return updated_count
