import re
from typing import Dict, Any, Optional, List

# The 3 canonical privacy / recognition modes
MODE_PUBLIC = "public"
MODE_SEMI_ANONYMOUS = "semi_anonymous"
MODE_FULLY_ANONYMOUS = "fully_anonymous"

VALID_MODES = [MODE_PUBLIC, MODE_SEMI_ANONYMOUS, MODE_FULLY_ANONYMOUS]

def classify_recognition_mode(raw_input: Optional[str]) -> str:
    """
    Rule-Based Privacy Classifier.
    Maps raw Google Form text or database recognition strings into one of the 3 canonical modes:
    1. 'public' - Show Name & Contributed Amount on website dashboard
    2. 'semi_anonymous' - Show Name only, Hide Amount
    3. 'fully_anonymous' - Keep contribution completely anonymous
    """
    if not raw_input:
        return MODE_SEMI_ANONYMOUS

    text = str(raw_input).strip().lower()

    # Priority 1: Semi-Anonymous (Check explicitly before general 'anonymous' keyword)
    if any(k in text for k in [
        "semi-anonymous", "semi_anonymous", "semi anonymous", "semi",
        "hide amount", "show my name only", "name only", "name_only",
        "name and batch", "name_and_batch", "name and organization",
        "name_and_organization", "show name"
    ]):
        return MODE_SEMI_ANONYMOUS

    # Priority 2: Fully Anonymous (Keep contribution completely anonymous)
    if any(k in text for k in [
        "fully anonymous", "completely anonymous", "keep contribution completely anonymous",
        "anonymous", "anon", "private", "hide name", "hide all", "do not disclose"
    ]):
        return MODE_FULLY_ANONYMOUS

    # Priority 3: Public (Explicitly requested name AND amount on dashboard)
    if any(k in text for k in [
        "public", "show my name & contributed amount", "show my name and contributed amount",
        "show name and amount", "name and amount", "full recognition", "full_recognition",
        "amount on website", "public supporter", "full"
    ]):
        return MODE_PUBLIC

    # Default fallback to Semi-Anonymous for safe privacy preservation
    return MODE_SEMI_ANONYMOUS


def project_public_contribution(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rule-Based Public Projection Filter for a single contribution record.
    Enforces strict privacy transformations and strips all confidential metadata
    (email, phone, transaction references, payment proofs).
    """
    raw_mode = record.get("recognition_type") or record.get("recognition_preference")
    mode = classify_recognition_mode(raw_mode)
    
    raw_name = record.get("full_name") or "SC&SS Alumnus"
    raw_amount = record.get("amount")
    try:
        numeric_amount = float(raw_amount) if raw_amount is not None else 0.0
    except (ValueError, TypeError):
        numeric_amount = 0.0

    raw_batch = record.get("graduation_year")
    raw_course = record.get("course")
    submitted_at = record.get("submitted_at") or record.get("created_at")

    if mode == MODE_PUBLIC:
        return {
            "id": record.get("id"),
            "display_name": raw_name.strip(),
            "graduation_year": raw_batch,
            "course": raw_course,
            "amount": numeric_amount,
            "amount_formatted": f"₹{numeric_amount:,.2f}" if numeric_amount > 0 else "Support Contribution",
            "is_amount_visible": True,
            "is_name_visible": True,
            "privacy_mode": MODE_PUBLIC,
            "privacy_label": "Public Contributor",
            "badge_class": "badge-public",
            "submitted_at": submitted_at
        }

    elif mode == MODE_SEMI_ANONYMOUS:
        return {
            "id": record.get("id"),
            "display_name": raw_name.strip(),
            "graduation_year": raw_batch,
            "course": raw_course,
            "amount": None,
            "amount_formatted": "Undisclosed Contribution",
            "is_amount_visible": False,
            "is_name_visible": True,
            "privacy_mode": MODE_SEMI_ANONYMOUS,
            "privacy_label": "Supporter (Amount Hidden)",
            "badge_class": "badge-semi",
            "submitted_at": submitted_at
        }

    else:  # MODE_FULLY_ANONYMOUS
        return {
            "id": record.get("id"),
            "display_name": "Anonymous Alumnus",
            "graduation_year": None,  # Suppressed to avoid batch deanonymization
            "course": None,
            "amount": None,
            "amount_formatted": "Undisclosed Contribution",
            "is_amount_visible": False,
            "is_name_visible": False,
            "privacy_mode": MODE_FULLY_ANONYMOUS,
            "privacy_label": "Anonymous Contributor",
            "badge_class": "badge-anon",
            "submitted_at": submitted_at
        }


def project_public_contributions_list(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply the privacy rule engine across an entire collection of contributor records."""
    return [project_public_contribution(r) for r in records]
