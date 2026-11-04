import pytest
from unittest.mock import patch
from app import create_app
from config import Config

class RouteTestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    ADMIN_PATH_PREFIX = "/admin"

@pytest.fixture
def client():
    app = create_app(RouteTestConfig)
    with app.test_client() as client:
        yield client

def test_public_homepage(client):
    """Verify public homepage renders successfully."""
    with patch("routes.public.get_current_meet_context") as mock_meet_ctx, \
         patch("routes.public.get_distinct_batches", return_value=[2010, 2015, 2020]):
        mock_meet_ctx.return_value = {
            "meet": {
                "id": 1,
                "name": "SC&SS JNU Alumni Meet 2026",
                "description": "Annual Gathering",
                "event_date": None,
                "venue": "SC&SS Auditorium, JNU, New Delhi",
                "status": "registration_open"
            },
            "stats": {"total_responses": 10, "total_attending_alumni": 8, "total_headcount": 12, "total_guests": 4}
        }
        res = client.get("/")
        assert res.status_code == 200
        assert b"SC&amp;SS" in res.data or b"SC&SS" in res.data
        assert b"Alumni Meet 2026" in res.data

def test_public_meet_page(client):
    """Verify meet schedule page renders."""
    with patch("routes.public.get_current_meet_context") as mock_meet_ctx:
        mock_meet_ctx.return_value = {
            "meet": {
                "id": 1,
                "name": "SC&SS JNU Alumni Meet 2026",
                "description": "Annual Gathering",
                "event_date": None,
                "venue": "SC&SS Auditorium",
                "status": "registration_open"
            },
            "stats": {"total_responses": 0, "total_attending_alumni": 0, "total_headcount": 0, "total_guests": 0}
        }
        res = client.get("/meet")
        assert res.status_code == 200
        assert b"Schedule" in res.data

def test_public_about_redirects_to_homepage_section(client):
    """The /about page was merged into the homepage; old links must keep working."""
    res = client.get("/about")
    assert res.status_code == 301
    assert res.headers["Location"].endswith("/#about")

def test_public_gallery_page(client):
    """Gallery renders Drive-hosted thumbnails, never images served by this app."""
    with patch("routes.public.get_public_gallery") as mock_gallery:
        mock_gallery.return_value = {
            "photos": [{
                "id": 1,
                "drive_file_id": "1AbCdEfGhIjKlMnOpQrStUvWxYz",
                "caption": "Batch of 1998 reunion",
                "album": "Reunions",
                "thumb_url": "https://drive.google.com/thumbnail?id=1AbCdEfGhIjKlMnOpQrStUvWxYz&sz=w480",
                "full_url": "https://drive.google.com/thumbnail?id=1AbCdEfGhIjKlMnOpQrStUvWxYz&sz=w1600",
            }],
            "albums": ["Reunions"],
            "selected_album": None,
            "page": 1,
            "total": 1,
            "has_next": False,
            "has_prev": False,
        }
        res = client.get("/gallery?album=Reunions&page=2")
        assert res.status_code == 200
        mock_gallery.assert_called_once_with(album="Reunions", page=2)
        assert b"drive.google.com/thumbnail?id=1AbCdEfGhIjKlMnOpQrStUvWxYz&amp;sz=w480" in res.data
        assert b"Batch of 1998 reunion" in res.data

def test_public_gallery_empty_state(client):
    with patch("routes.public.get_public_gallery") as mock_gallery:
        mock_gallery.return_value = {
            "photos": [], "albums": [], "selected_album": None,
            "page": 1, "total": 0, "has_next": False, "has_prev": False,
        }
        res = client.get("/gallery")
        assert res.status_code == 200
        assert b"Photos coming soon" in res.data

def test_inline_editor_saves_to_the_page_being_edited(client):
    """Bare keys like hero_title exist on several pages; they must resolve against the posted page."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    sections = [
        {"id": 10, "page": "index", "section_key": "hero_title"},
        {"id": 20, "page": "meet", "section_key": "hero_title"},
        {"id": 30, "page": "event", "section_key": "date"},
    ]
    with patch("routes.admin.get_sections_for_admin", return_value=sections),          patch("routes.admin.bulk_update_sections", return_value=2) as mock_bulk:
        res = client.post("/admin/sections/ajax-update", json={
            "page": "index",
            "updates": {"hero_title": "Home Title", "event.date": "Saturday, 5 December 2026"}
        })
        assert res.status_code == 200
        updates = mock_bulk.call_args[0][0]
        assert updates == {10: "Home Title", 30: "Saturday, 5 December 2026"}

def test_public_contribute_page(client):
    """Verify contribute page renders."""
    with patch("routes.public.get_current_meet_context") as mock_meet_ctx:
        mock_meet_ctx.return_value = {
            "meet": {"id": 1, "name": "SC&SS JNU Alumni Meet 2026"},
            "stats": {}
        }
        res = client.get("/contribute")
        assert res.status_code == 200
        assert b"Support the SC&amp;SS Alumni Meet 2026" in res.data or b"Support the SC&SS Alumni Meet 2026" in res.data

def test_public_api_alumni_json(client):
    """Verify JSON endpoint for public alumni directory."""
    with patch("routes.api.get_public_alumni_directory") as mock_dir:
        mock_dir.return_value = [
            {"id": 1, "full_name": "Test Alumnus", "graduation_year": 2015, "course": "MCA"}
        ]
        res = client.get("/api/public/alumni")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["count"] == 1
        assert data["data"][0]["full_name"] == "Test Alumnus"

def test_admin_dashboard_auth_redirect(client):
    """Verify that unauthenticated access to /admin redirects to /admin/login."""
    res = client.get("/admin/")
    assert res.status_code == 302
    assert "/admin/login" in res.headers["Location"]

def test_custom_configurable_admin_path():
    """Verify that changing ADMIN_PATH_PREFIX dynamically re-binds admin routes."""
    from app import create_app
    from config import Config
    
    class CustomConfig(Config):
        TESTING = True
        ADMIN_PATH_PREFIX = "/secret-organizer-portal"
        SECRET_KEY = "test-secret"
        
    custom_app = create_app(CustomConfig)
    with custom_app.test_client() as custom_client:
        # Default /admin should 404 when prefix is changed
        res_old = custom_client.get("/admin/")
        assert res_old.status_code == 404
        
        # New configurable path should redirect to /secret-organizer-portal/login
        res_new = custom_client.get("/secret-organizer-portal/")
        assert res_new.status_code == 302
        assert "/secret-organizer-portal/login" in res_new.headers["Location"]
        
        # Accessing login page on custom path
        res_login = custom_client.get("/secret-organizer-portal/login")
        assert res_login.status_code == 200
        assert b"Organizer Portal" in res_login.data
