import pytest
from unittest.mock import patch, MagicMock
from services.auth_service import hash_password, verify_password, authenticate_user
from services.contribution_service import process_contribution_verification
from services.drive_service import extract_google_drive_file_id, get_drive_preview_url

def test_password_hashing_and_verification():
    """Verify password hashing with PBKDF2/SHA256."""
    password = "SuperSecretPassword123!"
    p_hash = hash_password(password)
    assert p_hash != password
    assert verify_password(password, p_hash) is True
    assert verify_password("WrongPassword", p_hash) is False

def test_user_authentication():
    """Verify user authentication logic."""
    p_hash = hash_password("ValidPassword")
    mock_user = {
        "id": 1,
        "email": "organizer@scss.jnu.ac.in",
        "password_hash": p_hash,
        "full_name": "Test Organizer",
        "role": "organizer",
        "is_active": 1
    }

    with patch("services.auth_service.get_user_by_email", return_value=mock_user):
        # Successful authentication
        user = authenticate_user("organizer@scss.jnu.ac.in", "ValidPassword")
        assert user is not None
        assert user["id"] == 1

        # Invalid password
        assert authenticate_user("organizer@scss.jnu.ac.in", "WrongPassword") is None

    with patch("services.auth_service.get_user_by_email", return_value=None):
        # Non-existent user
        assert authenticate_user("unknown@scss.jnu.ac.in", "ValidPassword") is None

def test_drive_service_url_parsing():
    """Verify Google Drive File ID extraction."""
    # Direct File ID
    file_id = "1a2B3c4D5e6F7g8H9i0J"
    assert extract_google_drive_file_id(file_id) == file_id
    assert get_drive_preview_url(file_id) == f"https://drive.google.com/file/d/{file_id}/view"

    # URL format with /file/d/
    url1 = "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2up0Y/view"
    assert extract_google_drive_file_id(url1) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2up0Y"

    # URL format with id=
    url2 = "https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2up0Y"
    assert extract_google_drive_file_id(url2) == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2up0Y"

def test_process_contribution_verification():
    """Verify contribution verification state transition and audit trail recording."""
    mock_contrib = {
        "id": 42,
        "amount": 10000.00,
        "payment_status": "submitted",
        "alumni_id": 5
    }

    with patch("services.contribution_service.get_contribution_by_id", return_value=mock_contrib), \
         patch("services.contribution_service.update_contribution_status", return_value=True) as mock_update, \
         patch("services.contribution_service.log_audit_action", return_value=1) as mock_audit:

        # Test verification
        result = process_contribution_verification(42, "verify", user_id=1, notes="Bank credited")
        assert result["success"] is True
        assert result["new_status"] == "verified"
        mock_update.assert_called_once_with(contrib_id=42, status="verified", verified_by=1, notes="Bank credited")
        mock_audit.assert_called_once()
