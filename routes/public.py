import threading
import time
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from services.meet_service import get_current_meet_context
from services.contribution_service import get_public_contributions_tracker
from services.gallery_service import get_public_gallery, get_gallery_preview
from db.alumni import get_distinct_batches, get_distinct_courses
from config import Config

public_bp = Blueprint("public", __name__)

# Public pages run several sequential TiDB queries (~0.09s each). Their data only changes
# through the daily sheet sync or admin edits, so keep it briefly per process.
# Any admin form submission clears it (see routes/admin.py), so edits show up immediately.
PUBLIC_CACHE_SECONDS = 60
PUBLIC_CACHE_MAX_ENTRIES = 200
_public_cache = {}
_public_cache_lock = threading.Lock()

def clear_public_cache():
    with _public_cache_lock:
        _public_cache.clear()

def _cached(key, loader):
    """Return a cached value for key, or compute it with loader(). Bypassed in tests."""
    if current_app.testing:
        return loader()
    now = time.monotonic()
    with _public_cache_lock:
        hit = _public_cache.get(key)
        if hit is not None and hit[0] > now:
            return hit[1]
    value = loader()
    with _public_cache_lock:
        if len(_public_cache) >= PUBLIC_CACHE_MAX_ENTRIES:
            _public_cache.clear()
        _public_cache[key] = (now + PUBLIC_CACHE_SECONDS, value)
    return value

@public_bp.route("/ping")
@public_bp.route("/health")
@public_bp.route("/healthz")
def keep_alive_ping():
    """Keep-alive endpoint for Render cron jobs & uptime monitors."""
    return "ok", 200, {"Content-Type": "text/plain; charset=utf-8"}

@public_bp.route("/")
def index():
    """Homepage: meet hero, contribution tracker, about the meet & school, gallery teaser."""
    context = _cached("meet_context", get_current_meet_context)
    meet_id = context["meet"]["id"]
    tracker = _cached(("tracker", meet_id), lambda: get_public_contributions_tracker(meet_id=meet_id))

    return render_template(
        "index.html",
        meet=context["meet"],
        stats=context["stats"],
        tracker=tracker,
        gallery_preview=_cached("gallery_preview", lambda: get_gallery_preview(limit=6)),
        google_form_url=Config.GOOGLE_FORM_URL
    )

@public_bp.route("/meet")
def meet_detail():
    """Alumni Meet details, schedule, venue, and registration guide."""
    context = _cached("meet_context", get_current_meet_context)
    return render_template(
        "meet.html",
        meet=context["meet"],
        stats=context["stats"],
        google_form_url=Config.GOOGLE_FORM_URL
    )

@public_bp.route("/invite")
def invite():
    """Public, shareable invitation page with the official poster (link previews show the poster)."""
    return render_template("invite.html")

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
        gallery=_cached(("gallery", album, page), lambda: get_public_gallery(album=album, page=page))
    )

@public_bp.route("/alumni")
def alumni_directory():
    """Public alumni directory is paused during registration/contribution drive."""
    return redirect(url_for("public.contribute"))

@public_bp.route("/contributions")
@public_bp.route("/contribute")
def contribute():
    """Contribution Tracker & Supporter Transparency Hub."""
    context = _cached("meet_context", get_current_meet_context)
    meet_id = context["meet"]["id"]
    tracker = _cached(("tracker", meet_id), lambda: get_public_contributions_tracker(meet_id=meet_id))
    batches = _cached("batches", get_distinct_batches)
    courses = _cached("courses", get_distinct_courses)

    return render_template(
        "contribute.html",
        meet=context["meet"],
        tracker=tracker,
        batches=batches,
        courses=courses,
        google_form_url=Config.GOOGLE_FORM_URL
    )
