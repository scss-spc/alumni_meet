from flask import Blueprint, render_template, request, redirect, url_for, flash, session
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
    delete_single_contribution,
    clean_duplicate_contributions
)
from services.drive_service import get_drive_preview_url, get_drive_thumbnail_url
from services.sync_service import get_sync_status, perform_sync, test_sheet_connection
from services.scheduler_service import get_scheduler_info
from services.gallery_service import (
    get_admin_gallery,
    add_gallery_photos,
    toggle_photo_published,
    edit_photo,
    remove_photo
)
from db.meets import get_meet_responses_admin
from db.contributions import get_contribution_stats
from services.expense_service import (
    EXPENSE_AUDIENCES,
    EXPENSE_CATEGORIES,
    add_payment,
    build_expense_summary,
    get_expense_with_payments,
    list_expenses,
    parse_expense_form,
    parse_payment_form,
    remove_expense,
    remove_payment,
    save_expense
)
from db.audit import get_recent_audit_logs

admin_bp = Blueprint("admin", __name__)

@admin_bp.after_request
def _refresh_public_pages_after_admin_change(response):
    """Admin edits (gallery, contributions, sections, ...) must show on public pages immediately."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        from routes.public import clear_public_cache
        from db.sections import invalidate_sections_cache
        clear_public_cache()
        invalidate_sections_cache()
    return response

@admin_bp.route("/", methods=["GET", "POST"])
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Single organizer portal entry point (e.g. /secret-portal). Renders login when logged out, dashboard when logged in."""
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

@admin_bp.route("/dashboard")
@login_required
def dashboard():
    """Operational Overview Dashboard & Portal Hub."""
    meet_ctx = get_current_meet_context()
    meet_id = meet_ctx["meet"]["id"]

    contrib_data = get_contributions_dashboard(meet_id=meet_id, per_page=5)
    recent_responses = get_meet_responses_admin(meet_id=meet_id, limit=5)
    audit_logs = get_recent_audit_logs(limit=5)
    sync_state = get_sync_status()
    scheduler_info = get_scheduler_info()
    try:
        expense_summary = build_expense_summary(
            meet_id, meet_ctx["stats"], contrib_data["stats"].get("total_submitted_amount")
        )
    except Exception:
        expense_summary = None  # e.g. expenses table not created yet

    return render_template(
        "admin/dashboard.html",
        expense_summary=expense_summary,
        meet=meet_ctx["meet"],
        meet_stats=meet_ctx["stats"],
        financial_stats=contrib_data["stats"],
        recent_contributions=contrib_data["records"],
        recent_responses=recent_responses,
        audit_logs=audit_logs,
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
    """Contribution list with search."""
    search = request.args.get("search", "").strip() or None
    page = request.args.get("page", 1, type=int)

    data = get_contributions_dashboard(
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
        current_search=search or ""
    )

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


@admin_bp.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    """Spending on alumni: catering (per head), mementos (per alumnus) and other costs."""
    meet_ctx = get_current_meet_context()
    meet_id = meet_ctx["meet"]["id"]

    if request.method == "POST":
        data, errors = parse_expense_form(request.form, meet_id)
        if errors:
            for err in errors:
                flash(err, "danger")
        else:
            expense_id = request.form.get("id", type=int)
            saved_id, error = save_expense(data, expense_id=expense_id, user_id=session.get("user_id"))
            if error:
                flash(error, "danger")
            else:
                flash("Expense updated." if expense_id else "Expense added.", "success")
        return redirect(url_for("admin.expenses", category=request.args.get("category") or None,
                                audience=request.args.get("audience") or None))

    category = request.args.get("category", "").strip() or None
    if category not in EXPENSE_CATEGORIES:
        category = None
    audience = request.args.get("audience", "").strip() or None
    if audience not in EXPENSE_AUDIENCES:
        audience = None
    funds = get_contribution_stats(meet_id=meet_id).get("total_submitted_amount")
    all_expenses = list_expenses(meet_id)
    return render_template(
        "admin/expenses.html",
        meet=meet_ctx["meet"],
        meet_stats=meet_ctx["stats"],
        summary=build_expense_summary(meet_id, meet_ctx["stats"], funds, expenses=all_expenses),
        expenses=[e for e in all_expenses
                  if (not category or e["category"] == category) and (not audience or e["audience"] == audience)],
        categories=EXPENSE_CATEGORIES,
        audiences=EXPENSE_AUDIENCES,
        current_category=category or "",
        current_audience=audience or ""
    )

@admin_bp.route("/expenses/<int:expense_id>/payments", methods=["POST"])
@login_required
def add_expense_payment_route(expense_id: int):
    """Record a part or full payment against an expense."""
    expense = get_expense_with_payments(expense_id)
    if not expense:
        flash("Expense not found.", "warning")
        return redirect(url_for("admin.expenses"))
    payment, errors = parse_payment_form(request.form, expense["balance_due"])
    if errors:
        for err in errors:
            flash(err, "danger")
    else:
        add_payment(expense_id, payment, user_id=session.get("user_id"))
        remaining = expense["balance_due"] - payment["amount"]
        if remaining <= 0:
            flash(f"Payment recorded. \"{expense['description']}\" is now fully paid.", "success")
        else:
            flash(f"Part payment recorded. ₹{remaining:,.2f} still due on \"{expense['description']}\".", "success")
    return redirect(request.referrer or url_for("admin.expenses"))

@admin_bp.route("/expenses/payments/<int:payment_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_expense_payment_route(payment_id: int):
    """Remove a wrongly recorded payment (admins only)."""
    try:
        removed = remove_payment(payment_id, user_id=session.get("user_id"))
        flash("Payment removed." if removed else "Payment not found or already removed.",
              "success" if removed else "warning")
    except Exception as e:
        flash(f"Error removing payment: {str(e)}", "danger")
    return redirect(request.referrer or url_for("admin.expenses"))

@admin_bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_expense_route(expense_id: int):
    """Delete an expense entry (admins only)."""
    try:
        removed = remove_expense(expense_id, user_id=session.get("user_id"))
        if removed:
            flash(f"Deleted expense: {removed.get('description')}.", "success")
        else:
            flash("Expense not found or already deleted.", "warning")
    except Exception as e:
        flash(f"Error deleting expense: {str(e)}", "danger")
    return redirect(request.referrer or url_for("admin.expenses"))

@admin_bp.route("/gallery", methods=["GET", "POST"])
@login_required
def gallery():
    """Gallery management. Photos stay on Google Drive; only their file IDs are stored here."""
    if request.method == "POST":
        result = add_gallery_photos(
            raw_links=request.form.get("drive_links", ""),
            caption=request.form.get("caption", "").strip(),
            album=request.form.get("album", "").strip(),
            user_id=session.get("user_id")
        )
        if result["added"]:
            flash(f"Added {result['added']} photo(s) to the gallery.", "success")
        if result["duplicates"]:
            flash(f"{result['duplicates']} photo(s) were already in the gallery and were skipped.", "info")
        if result["rejected"]:
            flash(
                f"{len(result['rejected'])} line(s) were not Drive file links and were skipped "
                f"(folder links are not supported): {', '.join(result['rejected'][:3])}",
                "danger"
            )
        if not (result["added"] or result["duplicates"] or result["rejected"]):
            flash("Paste at least one Google Drive photo link.", "danger")
        return redirect(url_for("admin.gallery"))

    return render_template("admin/gallery.html", **get_admin_gallery())

@admin_bp.route("/gallery/<int:photo_id>/publish", methods=["POST"])
@login_required
def gallery_toggle_publish(photo_id: int):
    is_published = request.form.get("is_published") == "1"
    toggle_photo_published(photo_id, is_published, user_id=session.get("user_id"))
    flash("Photo is now visible on the public gallery." if is_published else "Photo hidden from the public gallery.", "info")
    return redirect(url_for("admin.gallery"))

@admin_bp.route("/gallery/<int:photo_id>/edit", methods=["POST"])
@login_required
def gallery_edit_photo(photo_id: int):
    edit_photo(
        photo_id,
        caption=request.form.get("caption", "").strip(),
        album=request.form.get("album", "").strip(),
        user_id=session.get("user_id")
    )
    flash("Photo details updated.", "success")
    return redirect(url_for("admin.gallery"))

@admin_bp.route("/gallery/<int:photo_id>/delete", methods=["POST"])
@login_required
def gallery_delete_photo(photo_id: int):
    remove_photo(photo_id, user_id=session.get("user_id"))
    flash("Photo removed from the gallery. The file on Google Drive was not touched.", "info")
    return redirect(url_for("admin.gallery"))
