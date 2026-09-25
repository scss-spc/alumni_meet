import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from config import Config
from db.sections import (
    init_site_sections_table,
    get_all_sections,
    get_sections_dict,
    get_section_by_id,
    update_section,
    reset_section_to_default
)
from services.section_service import (
    get_sections_for_admin,
    update_single_section,
    reset_single_section,
    bulk_update_sections
)

class SectionTestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-sections-secret"
    ADMIN_PATH_PREFIX = "/admin"

@pytest.fixture
def client():
    app = create_app(SectionTestConfig)
    with app.test_client() as client:
        yield client

def test_db_sections_init_and_get():
    """Verify db/sections table initialization and retrieval."""
    init_site_sections_table()
    sections = get_all_sections()
    assert len(sections) > 0

    sec_dict = get_sections_dict()
    assert "index.hero_title" in sec_dict
    assert sec_dict["index.hero_title"] == "Alumni Meet 2026"

def test_update_and_reset_section():
    """Verify section update and reset to default value."""
    init_site_sections_table()
    sections = get_all_sections(page="index")
    hero_title_sec = next(s for s in sections if s["section_key"] == "hero_title")
    sec_id = hero_title_sec["id"]

    # Update section
    update_section(sec_id, "Custom Alumni Gathering 2026", updated_by=1)
    sec_updated = get_section_by_id(sec_id)
    assert sec_updated["content_value"] == "Custom Alumni Gathering 2026"

    sec_dict = get_sections_dict()
    assert sec_dict["index.hero_title"] == "Custom Alumni Gathering 2026"

    # Reset section
    reset_section_to_default(sec_id, updated_by=1)
    sec_reset = get_section_by_id(sec_id)
    assert sec_reset["content_value"] is None

    sec_dict_reset = get_sections_dict()
    assert sec_dict_reset["index.hero_title"] == "Alumni Meet 2026"

def test_service_bulk_update():
    """Verify bulk section updates via service layer."""
    init_site_sections_table()
    sections = get_sections_for_admin(selected_page="index")
    s1 = sections[0]
    s2 = sections[1]

    updates = {
        s1["id"]: "Service Update 1",
        s2["id"]: "Service Update 2"
    }

    count = bulk_update_sections(updates, user_id=1)
    assert count == 2

    # Verify updated values
    u1 = get_section_by_id(s1["id"])
    u2 = get_section_by_id(s2["id"])
    assert u1["content_value"] == "Service Update 1"
    assert u2["content_value"] == "Service Update 2"

    # Cleanup reset
    reset_single_section(s1["id"], user_id=1)
    reset_single_section(s2["id"], user_id=1)

def test_admin_sections_route_requires_login(client):
    """Verify /admin/sections requires authentication."""
    res = client.get("/admin/sections")
    assert res.status_code == 302
    assert "/admin/login" in res.headers["Location"]

def test_admin_sections_route_logged_in(client):
    """Verify authenticated admin can access /admin/sections and update sections."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Admin Test"
        sess["user_role"] = "admin"

    res = client.get("/admin/sections")
    assert res.status_code == 200
    assert b"Website Sections Editor" in res.data

    # Submit form POST to update section
    sections = get_sections_for_admin("index")
    sec_id = sections[0]["id"]

    post_data = {
        f"section_{sec_id}": "Form Submitted Heading Title"
    }
    res_post = client.post("/admin/sections?page=index", data=post_data, follow_redirects=True)
    assert res_post.status_code == 200
    assert b"Successfully saved changes" in res_post.data

    # Verify reset endpoint
    res_reset = client.post(f"/admin/sections/{sec_id}/reset", follow_redirects=True)
    assert res_reset.status_code == 200
    assert b"Section content reset to original default copy" in res_reset.data
