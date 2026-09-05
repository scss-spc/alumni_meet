import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from config import Config
from services.alumni_service import purge_all_alumni_records

class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-key"
    ADMIN_PATH_PREFIX = "/admin"

@pytest.fixture
def app():
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_purge_all_alumni_service():
    """Verify that purge_all_alumni_records calls DB purge and records audit log."""
    with patch("db.alumni.delete_all_alumni_data") as mock_delete, \
         patch("db.audit.log_audit_action") as mock_audit:
        mock_delete.return_value = {
            "alumni_deleted": 10,
            "contributions_deleted": 5,
            "responses_deleted": 8,
            "recognition_deleted": 10
        }
        
        metrics = purge_all_alumni_records(user_id=1)
        assert metrics["alumni_deleted"] == 10
        assert metrics["contributions_deleted"] == 5
        mock_delete.assert_called_once()
        mock_audit.assert_called_once()
        assert mock_audit.call_args[1]["action"] == "PURGE_ALL_ALUMNI"

def test_admin_purge_route_unauthenticated(client):
    """Unauthenticated users must be redirected to login."""
    res = client.post("/admin/alumni/purge-all", data={"confirmation": "DELETE"})
    assert res.status_code == 302
    assert "/admin/login" in res.headers["Location"]

def test_admin_purge_route_invalid_confirmation(client):
    """Admins must provide exact confirmation text 'DELETE'."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_role"] = "admin"
        sess["user_name"] = "Admin User"
        
    res = client.post("/admin/alumni/purge-all", data={"confirmation": "wrong_text"}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Deletion canceled" in res.data

def test_admin_purge_route_success(client):
    """Authorized admin sending 'DELETE' triggers purge."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_role"] = "admin"
        sess["user_name"] = "Admin User"
        
    with patch("routes.admin.purge_all_alumni_records") as mock_purge:
        mock_purge.return_value = {
            "alumni_deleted": 12,
            "contributions_deleted": 6,
            "responses_deleted": 10,
            "recognition_deleted": 12
        }
        res = client.post("/admin/alumni/purge-all", data={"confirmation": "DELETE"}, follow_redirects=True)
        assert res.status_code == 200
        mock_purge.assert_called_once_with(user_id=1)
        assert b"Successfully purged all alumni data" in res.data

def test_delete_single_alumnus_service():
    """Verify that delete_single_alumnus calls DB deletion and records audit log."""
    from services.alumni_service import delete_single_alumnus
    with patch("db.alumni.delete_alumnus_by_id") as mock_delete, \
         patch("db.audit.log_audit_action") as mock_audit:
        mock_delete.return_value = {
            "alumni_id": 42,
            "full_name": "Priya Sharma",
            "email": "priya@example.com",
            "graduation_year": 2018,
            "course": "MCA",
            "contributions_deleted": 1,
            "responses_deleted": 1,
            "recognition_deleted": 1
        }
        
        metrics = delete_single_alumnus(alumni_id=42, user_id=1)
        assert metrics["alumni_id"] == 42
        assert metrics["full_name"] == "Priya Sharma"
        mock_delete.assert_called_once_with(42)
        mock_audit.assert_called_once()
        assert mock_audit.call_args[1]["action"] == "DELETE_SINGLE_ALUMNUS"
        assert mock_audit.call_args[1]["entity_id"] == 42

def test_delete_single_alumnus_service_not_found():
    """Verify delete_single_alumnus returns None when ID does not exist."""
    from services.alumni_service import delete_single_alumnus
    with patch("db.alumni.delete_alumnus_by_id", return_value=None), \
         patch("db.audit.log_audit_action") as mock_audit:
        metrics = delete_single_alumnus(alumni_id=9999, user_id=1)
        assert metrics is None
        mock_audit.assert_not_called()

def test_admin_delete_single_unauthenticated(client):
    """Unauthenticated users cannot delete an alumnus."""
    res = client.post("/admin/alumni/42/delete")
    assert res.status_code == 302
    assert "/admin/login" in res.headers["Location"]

def test_admin_delete_single_unauthorized_organizer(client):
    """Organizers without admin role cannot delete an alumnus."""
    with client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["user_role"] = "organizer"
        sess["user_name"] = "Regular Organizer"

    res = client.post("/admin/alumni/42/delete", follow_redirects=True)
    assert res.status_code == 200
    assert b"You do not have administrative permissions" in res.data

def test_admin_delete_single_success(client):
    """Authorized admin can delete single alumnus."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_role"] = "admin"
        sess["user_name"] = "Admin User"

    with patch("routes.admin.delete_single_alumnus") as mock_del:
        mock_del.return_value = {
            "alumni_id": 42,
            "full_name": "Priya Sharma",
            "email": "priya@example.com",
            "graduation_year": 2018,
            "course": "MCA",
            "contributions_deleted": 1,
            "responses_deleted": 1,
            "recognition_deleted": 1
        }
        res = client.post("/admin/alumni/42/delete", follow_redirects=True)
        assert res.status_code == 200
        mock_del.assert_called_once_with(alumni_id=42, user_id=1)
        assert b"Successfully deleted alumnus &#39;Priya Sharma&#39;" in res.data or b"Successfully deleted alumnus 'Priya Sharma'" in res.data

def test_admin_delete_single_not_found(client):
    """Deleting non-existent alumnus shows warning."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_role"] = "admin"
        sess["user_name"] = "Admin User"

    with patch("routes.admin.delete_single_alumnus", return_value=None):
        res = client.post("/admin/alumni/999/delete", follow_redirects=True)
        assert res.status_code == 200
        assert b"not found or already deleted" in res.data

def test_delete_single_contribution_service():
    """Verify that delete_single_contribution calls DB deletion and records audit log."""
    from services.contribution_service import delete_single_contribution
    with patch("db.contributions.delete_contribution_by_id") as mock_delete, \
         patch("services.contribution_service.log_audit_action") as mock_audit:
        mock_delete.return_value = {
            "id": 105,
            "alumni_id": 42,
            "amount": 500.0,
            "payment_status": "submitted",
            "transaction_reference": None
        }
        
        res = delete_single_contribution(contrib_id=105, user_id=1)
        assert res["id"] == 105
        mock_delete.assert_called_once_with(105)
        mock_audit.assert_called_once()
        assert mock_audit.call_args[1]["action"] == "DELETE_CONTRIBUTION"

def test_admin_delete_contribution_success(client):
    """Authorized admin can delete a single contribution."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_role"] = "admin"
        sess["user_name"] = "Admin User"

    with patch("routes.admin.delete_single_contribution") as mock_del:
        mock_del.return_value = {
            "id": 105,
            "amount": 500.0
        }
        res = client.post("/admin/contributions/105/delete", follow_redirects=True)
        assert res.status_code == 200
        mock_del.assert_called_once_with(contrib_id=105, user_id=1)
        assert b"Successfully deleted contribution #105" in res.data

def test_admin_deduplicate_contributions_route(client):
    """Admin can trigger contribution deduplication."""
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_role"] = "admin"
        sess["user_name"] = "Admin User"

    with patch("routes.admin.clean_duplicate_contributions") as mock_dedup:
        mock_dedup.return_value = {"duplicates_removed": 3}
        res = client.post("/admin/contributions/deduplicate", follow_redirects=True)
        assert res.status_code == 200
        mock_dedup.assert_called_once()
        assert b"Successfully removed 3 duplicate contribution record(s)" in res.data


