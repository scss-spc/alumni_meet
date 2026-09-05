import pytest
from unittest.mock import patch
from services.privacy_service import (
    classify_recognition_mode,
    project_public_contribution,
    project_public_contributions_list,
    MODE_PUBLIC,
    MODE_SEMI_ANONYMOUS,
    MODE_FULLY_ANONYMOUS
)
from services.contribution_service import get_public_contributions_tracker
from app import create_app

def test_classify_recognition_mode():
    """Test classification of varied raw form input into the 3 canonical privacy modes."""
    # Public
    assert classify_recognition_mode("Public") == MODE_PUBLIC
    assert classify_recognition_mode("Show my Name & Contributed Amount on the website dashboard") == MODE_PUBLIC
    assert classify_recognition_mode("Show my name and contributed amount") == MODE_PUBLIC
    assert classify_recognition_mode("Full Recognition") == MODE_PUBLIC
    assert classify_recognition_mode("full_recognition") == MODE_PUBLIC

    # Semi-Anonymous
    assert classify_recognition_mode("Semi-Anonymous") == MODE_SEMI_ANONYMOUS
    assert classify_recognition_mode("Show my Name only, hide amount") == MODE_SEMI_ANONYMOUS
    assert classify_recognition_mode("Name Only") == MODE_SEMI_ANONYMOUS
    assert classify_recognition_mode("name_and_batch") == MODE_SEMI_ANONYMOUS
    assert classify_recognition_mode("Name and Organization") == MODE_SEMI_ANONYMOUS
    assert classify_recognition_mode(None) == MODE_SEMI_ANONYMOUS

    # Fully Anonymous
    assert classify_recognition_mode("Fully Anonymous") == MODE_FULLY_ANONYMOUS
    assert classify_recognition_mode("Keep contribution completely anonymous") == MODE_FULLY_ANONYMOUS
    assert classify_recognition_mode("Anonymous") == MODE_FULLY_ANONYMOUS
    assert classify_recognition_mode("completely anonymous") == MODE_FULLY_ANONYMOUS
    assert classify_recognition_mode("hide name and amount") == MODE_FULLY_ANONYMOUS

def test_project_public_contribution_public_tier():
    """Test Public Contributor rule: exposes Name, Batch, and Amount."""
    raw_record = {
        "id": 101,
        "full_name": "Vikash Kumar",
        "email": "vikash@scss.jnu.ac.in",
        "phone": "+91 9999988888",
        "graduation_year": 2020,
        "course": "MCA",
        "amount": 7000.0,
        "transaction_reference": "UPI/SECRET/UTR/123",
        "payment_screenshot_path": "https://drive.google.com/open?id=sensitive_file",
        "recognition_type": "Show my Name & Contributed Amount on the website dashboard"
    }

    projected = project_public_contribution(raw_record)

    assert projected["display_name"] == "Vikash Kumar"
    assert projected["graduation_year"] == 2020
    assert projected["course"] == "MCA"
    assert projected["amount"] == 7000.0
    assert projected["amount_formatted"] == "₹7,000.00"
    assert projected["is_amount_visible"] is True
    assert projected["is_name_visible"] is True
    assert projected["privacy_mode"] == MODE_PUBLIC
    assert projected["badge_class"] == "badge-public"

    # Strict Privacy Invariants: No sensitive identifiers leaked
    assert "email" not in projected
    assert "phone" not in projected
    assert "transaction_reference" not in projected
    assert "payment_screenshot_path" not in projected

def test_project_public_contribution_semi_anonymous_tier():
    """Test Semi-Anonymous Contributor rule: exposes Name & Batch, but strictly HIDES Amount."""
    raw_record = {
        "id": 102,
        "full_name": "Priya Sharma",
        "email": "priya@gmail.com",
        "phone": "9876543210",
        "graduation_year": 2018,
        "course": "M.Tech CS",
        "amount": 15000.0,
        "transaction_reference": "UPI/SECRET/UTR/456",
        "payment_screenshot_path": "https://drive.google.com/open?id=sensitive_file_2",
        "recognition_type": "Show my Name only, hide amount"
    }

    projected = project_public_contribution(raw_record)

    assert projected["display_name"] == "Priya Sharma"
    assert projected["graduation_year"] == 2018
    assert projected["course"] == "M.Tech CS"
    assert projected["amount"] is None
    assert projected["amount_formatted"] == "Undisclosed Contribution"
    assert projected["is_amount_visible"] is False
    assert projected["is_name_visible"] is True
    assert projected["privacy_mode"] == MODE_SEMI_ANONYMOUS
    assert projected["badge_class"] == "badge-semi"

    # Strict Invariants
    assert "email" not in projected
    assert "phone" not in projected
    assert "transaction_reference" not in projected

def test_project_public_contribution_fully_anonymous_tier():
    """Test Fully Anonymous Contributor rule: masks Name, Batch, and Amount."""
    raw_record = {
        "id": 103,
        "full_name": "Secret Alumnus",
        "email": "secret@alumni.jnu.ac.in",
        "phone": "1234567890",
        "graduation_year": 2012,
        "course": "Ph.D.",
        "amount": 50000.0,
        "transaction_reference": "UPI/SECRET/UTR/789",
        "payment_screenshot_path": "https://drive.google.com/open?id=sensitive_file_3",
        "recognition_type": "Keep contribution completely anonymous"
    }

    projected = project_public_contribution(raw_record)

    assert projected["display_name"] == "Anonymous Alumnus"
    assert projected["graduation_year"] is None  # Suppressed to prevent batch deanonymization
    assert projected["course"] is None
    assert projected["amount"] is None
    assert projected["amount_formatted"] == "Undisclosed Contribution"
    assert projected["is_amount_visible"] is False
    assert projected["is_name_visible"] is False
    assert projected["privacy_mode"] == MODE_FULLY_ANONYMOUS
    assert projected["badge_class"] == "badge-anon"

    # Strict Invariants
    assert "email" not in projected
    assert "phone" not in projected
    assert "transaction_reference" not in projected

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_public_contributions_tracker_api(client):
    """Test /api/public/contributions endpoint returns sanitized data."""
    mock_tracker_data = {
        "stats": {
            "total_raised": 25000.0,
            "target_amount": 500000.0,
            "progress_percent": 5.0,
            "total_contributors": 3
        },
        "contributors": [
            {"display_name": "Vikash", "amount": 7000.0, "is_amount_visible": True, "privacy_mode": "public"}
        ],
        "recent_contributors": []
    }

    with patch("routes.api.get_public_contributions_tracker", return_value=mock_tracker_data):
        res = client.get("/api/public/contributions")
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        assert data["data"]["stats"]["total_raised"] == 25000.0

def test_alumni_directory_redirection(client):
    """Verify /alumni redirects to /contribute since directory is currently unlisted."""
    res = client.get("/alumni")
    assert res.status_code == 302
    assert "/contribute" in res.headers["Location"]
