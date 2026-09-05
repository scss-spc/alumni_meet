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

def test_public_about_page(client):
    """Verify about page renders."""
    res = client.get("/about")
    assert res.status_code == 200
    assert b"School of Computer" in res.data

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
