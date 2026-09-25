from flask import Blueprint, jsonify, request, session
from services.auth_service import login_required
from services.contribution_service import process_contribution_verification, get_public_contributions_tracker
from services.alumni_service import get_public_alumni_directory
from services.sync_service import perform_sync, get_sync_status, test_sheet_connection
from services.scheduler_service import get_scheduler_info

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/health", methods=["GET"])
@api_bp.route("/ping", methods=["GET"])
def api_health():
    """API Keep-alive & Health Check endpoint."""
    return jsonify({"status": "ok", "service": "alumni-meet"}), 200

@api_bp.route("/public/contributions", methods=["GET"])
def public_contributions_json():
    """Sanitized public contributions tracker JSON endpoint applying the 3-tier privacy engine."""
    tracker = get_public_contributions_tracker()
    return jsonify({"success": True, "data": tracker})

@api_bp.route("/public/alumni", methods=["GET"])
def public_alumni_json():
    """Sanitized public alumni list endpoint (strict privacy preserved)."""
    search = request.args.get("search")
    batch = request.args.get("batch", type=int)
    course = request.args.get("course")

    data = get_public_alumni_directory(
        search=search,
        graduation_year=batch,
        course=course,
        limit=100
    )
    return jsonify({"success": True, "count": len(data), "data": data})

@api_bp.route("/admin/contributions/<int:contrib_id>/verify", methods=["POST"])
@login_required
def api_verify_contribution(contrib_id: int):
    """AJAX endpoint for quick verification."""
    data = request.get_json() or {}
    notes = data.get("notes")
    user_id = session.get("user_id")

    result = process_contribution_verification(
        contrib_id=contrib_id,
        action="verify",
        user_id=user_id,
        notes=notes
    )
    return jsonify(result)

@api_bp.route("/admin/contributions/<int:contrib_id>/reject", methods=["POST"])
@login_required
def api_reject_contribution(contrib_id: int):
    """AJAX endpoint for rejection."""
    data = request.get_json() or {}
    notes = data.get("notes")
    user_id = session.get("user_id")

    result = process_contribution_verification(
        contrib_id=contrib_id,
        action="reject",
        user_id=user_id,
        notes=notes
    )
    return jsonify(result)

@api_bp.route("/admin/sync/trigger", methods=["POST"])
@login_required
def api_trigger_sync():
    """Trigger an immediate Google Sheet sync with the database."""
    user_id = session.get("user_id")
    result = perform_sync(triggered_by="admin_dashboard", user_id=user_id)
    return jsonify(result), 200 if result.get("success") else 500

@api_bp.route("/admin/sync/status", methods=["GET"])
@login_required
def api_sync_status():
    """Get current sync state and scheduler status."""
    sync_state = get_sync_status()
    sched_info = get_scheduler_info()
    return jsonify({
        "success": True,
        "sync_state": sync_state,
        "scheduler": sched_info
    })

@api_bp.route("/admin/sync/test", methods=["POST"])
@login_required
def api_test_sheet_connection():
    """Test Google Sheet connectivity and preview columns."""
    result = test_sheet_connection()
    return jsonify(result), 200 if result.get("success") else 400
