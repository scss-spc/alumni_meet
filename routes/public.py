from flask import Blueprint, render_template, request, redirect, url_for
from services.meet_service import get_current_meet_context
from services.contribution_service import get_public_contributions_tracker
from services.gallery_service import get_public_gallery, get_gallery_preview
from db.alumni import get_distinct_batches, get_distinct_courses
from config import Config

public_bp = Blueprint("public", __name__)

@public_bp.route("/ping")
@public_bp.route("/health")
@public_bp.route("/healthz")
def keep_alive_ping():
    """Keep-alive endpoint for Render cron jobs & uptime monitors."""
    return "ok", 200, {"Content-Type": "text/plain; charset=utf-8"}

@public_bp.route("/")
def index():
    """Homepage: meet hero, contribution tracker, about the meet & school, gallery teaser."""
    context = get_current_meet_context()
    meet_id = context["meet"]["id"]
    tracker = get_public_contributions_tracker(meet_id=meet_id)

    return render_template(
        "index.html",
        meet=context["meet"],
        stats=context["stats"],
        tracker=tracker,
        gallery_preview=get_gallery_preview(limit=6),
        google_form_url=Config.GOOGLE_FORM_URL
    )

@public_bp.route("/meet")
def meet_detail():
    """Alumni Meet details, schedule, venue, and registration guide."""
    context = get_current_meet_context()
    return render_template(
        "meet.html",
        meet=context["meet"],
        stats=context["stats"],
        google_form_url=Config.GOOGLE_FORM_URL
    )

@public_bp.route("/about")
def about():
    """The School content now lives on the homepage; keep old links working."""
    return redirect(url_for("public.index", _anchor="about"), code=301)

@public_bp.route("/gallery")
def gallery():
    """Alumni photo gallery. Images are served by Google Drive, so Render only sends the HTML."""
    album = request.args.get("album", "").strip() or None
    page = request.args.get("page", 1, type=int) or 1
    return render_template(
        "gallery.html",
        gallery=get_public_gallery(album=album, page=page)
    )

@public_bp.route("/alumni")
def alumni_directory():
    """Public alumni directory is paused during registration/contribution drive."""
    return redirect(url_for("public.contribute"))

@public_bp.route("/contributions")
@public_bp.route("/contribute")
def contribute():
    """Contribution Tracker & Supporter Transparency Hub."""
    context = get_current_meet_context()
    meet_id = context["meet"]["id"]
    tracker = get_public_contributions_tracker(meet_id=meet_id)
    batches = get_distinct_batches()
    courses = get_distinct_courses()

    return render_template(
        "contribute.html",
        meet=context["meet"],
        tracker=tracker,
        batches=batches,
        courses=courses,
        google_form_url=Config.GOOGLE_FORM_URL
    )
