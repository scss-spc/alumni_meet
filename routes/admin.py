from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from services.auth_service import (
    authenticate_user,
    login_user_session,
    logout_user_session,
    login_required,
    admin_required,
    get_current_user
)
from services.meet_service import get_current_meet_context
from services.alumni_service import (
    get_admin_alumni_roster,
    get_alumnus_detail_admin,
    purge_all_alumni_records,
    delete_single_alumnus
)
from services.contribution_service import (
    get_contributions_dashboard,
    process_contribution_verification,
    delete_single_contribution,
    clean_duplicate_contributions
)
from services.volunteer_service import (
    get_volunteer_roster,
    save_volunteer,
    get_activities_overview,
    add_activity,
    assign_volunteer,
    unassign_volunteer
)
from services.drive_service import get_drive_preview_url, get_drive_thumbnail_url
from services.sync_service import get_sync_status, perform_sync, test_sheet_connection
from services.scheduler_service import get_scheduler_info
from db.meets import get_meet_responses_admin
from db.audit import get_recent_audit_logs

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Organizer & administrator login."""
    if session.get("user_id"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = authenticate_user(email, password)
        if user:
            login_user_session(user)
            flash(f"Welcome back, {user['full_name']}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin.dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("admin/login.html")

@admin_bp.route("/logout")
def logout():
    """Sign out organizer session."""
    logout_user_session()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("admin.login"))

@admin_bp.route("/")
@login_required
def dashboard():
    """Operational Overview Dashboard."""
    meet_ctx = get_current_meet_context()
    meet_id = meet_ctx["meet"]["id"]

    contrib_data = get_contributions_dashboard(meet_id=meet_id, per_page=5)
    recent_responses = get_meet_responses_admin(meet_id=meet_id, limit=5)
    audit_logs = get_recent_audit_logs(limit=5)
    volunteers = get_volunteer_roster(status="active")
    sync_state = get_sync_status()
    scheduler_info = get_scheduler_info()

    return render_template(
        "admin/dashboard.html",
        meet=meet_ctx["meet"],
        meet_stats=meet_ctx["stats"],
        financial_stats=contrib_data["stats"],
        recent_contributions=contrib_data["records"],
        recent_responses=recent_responses,
        audit_logs=audit_logs,
        volunteer_count=len(volunteers),
        sync_state=sync_state,
        scheduler_info=scheduler_info
    )

@admin_bp.route("/sync", methods=["GET", "POST"])
@login_required
def sync_management():
    """Google Sheet synchronization management and trigger page."""
    if request.method == "POST":
        action = request.form.get("action")
        if action == "sync_now":
            result = perform_sync(triggered_by="admin_sync_page", user_id=session.get("user_id"))
            if result.get("success"):
                flash(result.get("message", "Sync executed successfully."), "success")
            else:
                flash(f"Sync failed: {result.get('error')}", "danger")
            return redirect(url_for("admin.sync_management"))

    sync_state = get_sync_status()
    scheduler_info = get_scheduler_info()
    all_audit_logs = get_recent_audit_logs(limit=30)
    sync_logs = [log for log in all_audit_logs if log.get("action") == "google_sheet_sync"]

    return render_template(
        "admin/sync.html",
        sync_state=sync_state,
        scheduler_info=scheduler_info,
        sync_logs=sync_logs
    )

@admin_bp.route("/alumni")
@login_required
def alumni_list():
    """Full searchable alumni directory for organizers."""
    search = request.args.get("search", "").strip() or None
    batch = request.args.get("batch", type=int)
    course = request.args.get("course", "").strip() or None
    page = request.args.get("page", 1, type=int)

    roster = get_admin_alumni_roster(
        search=search,
        graduation_year=batch,
        course=course,
        page=page,
        per_page=25
    )

    return render_template(
        "admin/alumni.html",
        roster=roster,
        current_search=search or "",
        current_batch=batch,
        current_course=course or ""
    )

@admin_bp.route("/alumni/<int:alumni_id>")
@login_required
def alumni_detail(alumni_id: int):
    """Detailed view of an alumnus, attendance record, and payments."""
    detail = get_alumnus_detail_admin(alumni_id)
    if not detail:
        flash("Alumnus record not found.", "warning")
        return redirect(url_for("admin.alumni_list"))

    return render_template("admin/alumni_detail.html", detail=detail)

@admin_bp.route("/alumni/purge-all", methods=["POST"])
@login_required
@admin_required
def purge_all_alumni():
    """Danger zone: Purge all alumni details, RSVP responses, and contributions from the database."""
    confirmation = request.form.get("confirmation", "").strip().upper()
    if confirmation != "DELETE":
        flash("Deletion canceled: You must enter DELETE to confirm wiping all alumni data.", "warning")
        return redirect(url_for("admin.alumni_list"))

    try:
        user_id = session.get("user_id")
        metrics = purge_all_alumni_records(user_id=user_id)
        flash(
            f"Successfully purged all alumni data: {metrics['alumni_deleted']} alumni profiles, "
            f"{metrics['contributions_deleted']} contributions, and {metrics['responses_deleted']} RSVP responses deleted.",
            "success"
        )
    except Exception as e:
        flash(f"Error purging alumni records: {str(e)}", "danger")

    return redirect(url_for("admin.alumni_list"))

@admin_bp.route("/alumni/<int:alumni_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_alumnus(alumni_id: int):
    """Delete a single alumnus record, RSVP responses, and contributions."""
    try:
        user_id = session.get("user_id")
        metrics = delete_single_alumnus(alumni_id=alumni_id, user_id=user_id)
        if not metrics:
            flash(f"Alumnus ID #{alumni_id} not found or already deleted.", "warning")
        else:
            flash(
                f"Successfully deleted alumnus '{metrics['full_name']}' (ID #{alumni_id}) and associated records.",
                "success"
            )
    except Exception as e:
        flash(f"Error deleting alumnus record: {str(e)}", "danger")

    return redirect(url_for("admin.alumni_list"))


@admin_bp.route("/contributions")
@login_required
def contributions():
    """Contribution queue and verification management."""
    status = request.args.get("status", "").strip() or None
    search = request.args.get("search", "").strip() or None
    page = request.args.get("page", 1, type=int)

    data = get_contributions_dashboard(
        status=status,
        search=search,
        page=page,
        per_page=25
    )

    # Attach preview URL helper for templates
    for c in data["records"]:
        c["drive_preview_url"] = get_drive_preview_url(c.get("payment_screenshot_path"))

    return render_template(
        "admin/contributions.html",
        data=data,
        current_status=status or "",
        current_search=search or ""
    )

@admin_bp.route("/contributions/<int:contrib_id>/verify", methods=["POST"])
@login_required
def verify_contribution(contrib_id: int):
    """Mark contribution as verified."""
    notes = request.form.get("notes", "").strip() or None
    result = process_contribution_verification(
        contrib_id=contrib_id,
        action="verify",
        user_id=session["user_id"],
        notes=notes
    )
    if result["success"]:
        flash(f"Contribution #{contrib_id} marked as Verified.", "success")
    else:
        flash(result.get("error", "Failed to verify contribution."), "danger")
    return redirect(request.referrer or url_for("admin.contributions"))

@admin_bp.route("/contributions/<int:contrib_id>/reject", methods=["POST"])
@login_required
def reject_contribution(contrib_id: int):
    """Mark contribution as rejected."""
    notes = request.form.get("notes", "").strip() or None
    result = process_contribution_verification(
        contrib_id=contrib_id,
        action="reject",
        user_id=session["user_id"],
        notes=notes
    )
    if result["success"]:
        flash(f"Contribution #{contrib_id} marked as Rejected.", "warning")
    else:
        flash(result.get("error", "Failed to reject contribution."), "danger")
    return redirect(request.referrer or url_for("admin.contributions"))

@admin_bp.route("/contributions/<int:contrib_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_contribution_route(contrib_id: int):
    """Delete an invalid or duplicate contribution record."""
    try:
        user_id = session.get("user_id")
        contrib = delete_single_contribution(contrib_id=contrib_id, user_id=user_id)
        if not contrib:
            flash(f"Contribution #{contrib_id} not found or already deleted.", "warning")
        else:
            flash(f"Successfully deleted contribution #{contrib_id} ({contrib.get('amount')} INR).", "success")
    except Exception as e:
        flash(f"Error deleting contribution: {str(e)}", "danger")

    return redirect(request.referrer or url_for("admin.contributions"))

@admin_bp.route("/contributions/deduplicate", methods=["POST"])
@login_required
@admin_required
def deduplicate_contributions_route():
    """Scan and prune duplicate contribution records from database."""
    try:
        user_id = session.get("user_id")
        metrics = clean_duplicate_contributions(user_id=user_id)
        removed = metrics.get("duplicates_removed", 0)
        if removed > 0:
            flash(f"Successfully removed {removed} duplicate contribution record(s).", "success")
        else:
            flash("No duplicate contribution records found.", "info")
    except Exception as e:
        flash(f"Error deduplicating contributions: {str(e)}", "danger")

    return redirect(url_for("admin.contributions"))


@admin_bp.route("/volunteers", methods=["GET", "POST"])
@login_required
def volunteers():
    """Volunteer management (Independent of Alumni records)."""
    if request.method == "POST":
        data = {
            "id": request.form.get("id", type=int),
            "full_name": request.form.get("full_name", "").strip(),
            "email": request.form.get("email", "").strip() or None,
            "phone": request.form.get("phone", "").strip() or None,
            "role": request.form.get("role", "").strip() or None,
            "status": request.form.get("status", "active"),
            "notes": request.form.get("notes", "").strip() or None,
        }
        if not data["full_name"]:
            flash("Volunteer full name is required.", "danger")
        else:
            save_volunteer(data)
            flash("Volunteer saved successfully.", "success")
        return redirect(url_for("admin.volunteers"))

    search = request.args.get("search", "").strip() or None
    status = request.args.get("status", "").strip() or None
    volunteer_list = get_volunteer_roster(status=status, search=search)

    return render_template(
        "admin/volunteers.html",
        volunteers=volunteer_list,
        current_search=search or "",
        current_status=status or ""
    )

@admin_bp.route("/activities", methods=["GET", "POST"])
@login_required
def activities():
    """Organizing activities and volunteer assignment."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        if name:
            add_activity(meet_id=1, name=name, description=description)
            flash(f"Activity '{name}' created.", "success")
        return redirect(url_for("admin.activities"))

    activity_list = get_activities_overview(meet_id=1)
    volunteer_list = get_volunteer_roster(status="active")

    return render_template(
        "admin/activities.html",
        activities=activity_list,
        volunteers=volunteer_list
    )

@admin_bp.route("/activities/<int:activity_id>/assign", methods=["POST"])
@login_required
def assign_activity_volunteer(activity_id: int):
    """Assign volunteer to an organizing activity."""
    volunteer_id = request.form.get("volunteer_id", type=int)
    responsibility = request.form.get("responsibility", "").strip() or None
    if volunteer_id:
        assign_volunteer(activity_id, volunteer_id, responsibility)
        flash("Volunteer assigned to activity.", "success")
    return redirect(url_for("admin.activities"))

@admin_bp.route("/assignments/<int:assignment_id>/delete", methods=["POST"])
@login_required
def delete_assignment(assignment_id: int):
    """Remove a volunteer assignment."""
    unassign_volunteer(assignment_id)
    flash("Volunteer assignment removed.", "info")
    return redirect(url_for("admin.activities"))
