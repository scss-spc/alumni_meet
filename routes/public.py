from flask import Blueprint, render_template, request, redirect, url_for, current_app
from services.meet_service import get_current_meet_context
from services.contribution_service import get_public_contributions_tracker
from db.alumni import get_distinct_batches, get_distinct_courses
from config import Config

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    """Homepage: Academic & modern hero, meet info, contribution tracker milestone, and CTA."""
    context = get_current_meet_context()
    meet_id = context["meet"]["id"]
    tracker = get_public_contributions_tracker(meet_id=meet_id)
    batches = get_distinct_batches()

    return render_template(
        "index.html",
        meet=context["meet"],
        stats=context["stats"],
        tracker=tracker,
        batches=batches,
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
    """SC&SS and JNU history, legacy, and message from the school."""
    return render_template(
        "about.html",
        google_form_url=Config.GOOGLE_FORM_URL
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
