import pytest
from unittest.mock import patch, MagicMock
from services.auth_service import hash_password, verify_password, authenticate_user
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

def test_gallery_parse_drive_links():
    """Pasted Drive links become file IDs; folder links and junk are rejected; duplicates collapse."""
    from services.gallery_service import parse_drive_links
    raw = """
        https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view?usp=sharing
        https://drive.google.com/open?id=1ZyXwVuTsRqPoNmLkJiHgFeDcBa
        https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view
        https://drive.google.com/drive/folders/1FolderIdShouldBeRejected123
        not a link
    """
    file_ids, rejected = parse_drive_links(raw)
    assert file_ids == ["1AbCdEfGhIjKlMnOpQrStUvWxYz", "1ZyXwVuTsRqPoNmLkJiHgFeDcBa"]
    assert len(rejected) == 2
    assert any("folders" in r for r in rejected)

def test_public_gallery_groups_photos_by_album():
    """All-photos view: one section per album (in query order), then photos without an album."""
    import services.gallery_service as gs
    previews = [
        {"id": 3, "drive_file_id": "a" * 25, "caption": None, "album": "Batch of 2024", "album_total": 12},
        {"id": 2, "drive_file_id": "b" * 25, "caption": None, "album": "Batch of 2024", "album_total": 12},
        {"id": 1, "drive_file_id": "c" * 25, "caption": "Reunion", "album": "Meet 2026", "album_total": 1},
    ]
    loose = [{"id": 9, "drive_file_id": "d" * 25, "caption": None, "album": None}]
    with patch.object(gs, "get_album_previews", return_value=previews), \
         patch.object(gs, "get_photos", return_value=loose) as mock_get, \
         patch.object(gs, "count_photos", return_value=1), \
         patch.object(gs, "get_albums", return_value=["Batch of 2024", "Meet 2026"]):
        result = gs.get_public_gallery()
    assert [(g["name"], g["total"], len(g["photos"])) for g in result["groups"]] == [("Batch of 2024", 12, 2), ("Meet 2026", 1, 1)]
    assert mock_get.call_args.kwargs["ungrouped"] is True
    assert [p["id"] for p in result["photos"]] == [9]
