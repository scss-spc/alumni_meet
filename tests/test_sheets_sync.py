import pytest
from unittest.mock import patch, MagicMock
from services.sheets_service import (
    clean_header_text,
    detect_column_mapping,
    parse_year,
    parse_boolean_attending,
    parse_guest_count,
    parse_amount,
    parse_recognition_preference,
    GoogleSheetsConnector
)
from services.sync_service import perform_sync, get_sync_status
from services.scheduler_service import get_scheduler_info
from app import create_app

def test_clean_header_text():
    """Test header text cleanup removes brackets, punctuation, and extra whitespace."""
    assert clean_header_text("Full Name (as per degree)") == "full name"
    assert clean_header_text("Graduation Year / Batch (e.g. 2018)") == "graduation year batch"
    assert clean_header_text("Will you be attending the alumni meet?") == "will you be attending the alumni meet"

def test_detect_column_mapping():
    """Test flexible fuzzy mapping of Google Form headers to canonical DB field names."""
    headers = [
        "Timestamp",
        "Your Full Name",
        "Email Address",
        "WhatsApp / Mobile Number",
        "Year of Passing (Batch)",
        "Course / Degree Program",
        "Current Organization / Employer",
        "Designation / Job Title",
        "Current City of Residence",
        "Will you be attending the Alumni Meet?",
        "Number of Accompanying Guests",
        "Dietary Preference",
        "Suggestions / Messages for Batchmates",
        "Contribution Amount (INR)",
        "Transaction Reference / UTR ID",
        "Upload Payment Screenshot Link",
        "Public Recognition Preference"
    ]
    mapping = detect_column_mapping(headers)

    assert mapping["full_name"] == "Your Full Name"
    assert mapping["email"] == "Email Address"
    assert mapping["phone"] == "WhatsApp / Mobile Number"
    assert mapping["graduation_year"] == "Year of Passing (Batch)"
    assert mapping["course"] == "Course / Degree Program"
    assert mapping["organization"] == "Current Organization / Employer"
    assert mapping["designation"] == "Designation / Job Title"
    assert mapping["current_location"] == "Current City of Residence"
    assert mapping["attending"] == "Will you be attending the Alumni Meet?"
    assert mapping["guest_count"] == "Number of Accompanying Guests"
    assert mapping["dietary_preferences"] == "Dietary Preference"
    assert mapping["suggestions"] == "Suggestions / Messages for Batchmates"
    assert mapping["amount"] == "Contribution Amount (INR)"
    assert mapping["transaction_reference"] == "Transaction Reference / UTR ID"
    assert mapping["payment_screenshot_path"] == "Upload Payment Screenshot Link"
    assert mapping["recognition_type"] == "Public Recognition Preference"

def test_value_parsers():
    """Test robustness of individual value parsing helpers."""
    # Year
    assert parse_year("2018") == 2018
    assert parse_year("Batch 2020") == 2020
    assert parse_year(1995) == 1995
    assert parse_year("Invalid") is None

    # Attending
    assert parse_boolean_attending("Yes") is True
    assert parse_boolean_attending("YES") is True
    assert parse_boolean_attending("confirmed") is True
    assert parse_boolean_attending("No") is False
    assert parse_boolean_attending("cannot attend") is False
    assert parse_boolean_attending(None) is True

    # Guest Count
    assert parse_guest_count("0") == 0
    assert parse_guest_count("2 guests") == 2
    assert parse_guest_count(3) == 3
    assert parse_guest_count("") == 0

    # Amount
    assert parse_amount("5000") == 5000.0
    assert parse_amount("₹10,500.50") == 10500.50
    assert parse_amount("$250") == 250.0
    assert parse_amount(None) == 0.0

    # Recognition Preference
    assert parse_recognition_preference("Anonymous") == "fully_anonymous"
    assert parse_recognition_preference("Full Recognition (Name, Batch, Org)") == "public"
    assert parse_recognition_preference("Name and Batch Only") == "semi_anonymous"
    assert parse_recognition_preference("Name and Organization") == "semi_anonymous"
    assert parse_recognition_preference("Name Only") == "semi_anonymous"

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_perform_sync_with_mock_records():
    """Test full database sync pipeline with simulated normalized records."""
    mock_records = [
        {
            "row_number": 2,
            "full_name": "Sync Test Alumnus 1",
            "email": "synctest1@scss.jnu.ac.in",
            "phone": "+91 9876543210",
            "graduation_year": 2019,
            "course": "MCA",
            "organization": "Google India",
            "designation": "Staff Engineer",
            "current_location": "Bangalore",
            "attending": True,
            "guest_count": 1,
            "total_attendees": 2,
            "dietary_preferences": "Vegetarian",
            "suggestions": "Looking forward to meeting batchmates!",
            "amount": 5000.0,
            "transaction_reference": "UPI/SYNC/TEST/001",
            "payment_screenshot_path": "https://drive.google.com/file/d/test-file-id-1/view",
            "recognition_type": "full_recognition"
        },
        {
            "row_number": 3,
            "full_name": "Sync Test Alumnus 2",
            "email": "synctest2@scss.jnu.ac.in",
            "phone": "+91 9876543211",
            "graduation_year": 2015,
            "course": "M.Tech CS",
            "organization": "Microsoft",
            "designation": "Principal Architect",
            "current_location": "Hyderabad",
            "attending": False,
            "guest_count": 0,
            "total_attendees": 0,
            "dietary_preferences": None,
            "suggestions": "Cannot attend in person but wishing all the best.",
            "amount": 10000.0,
            "transaction_reference": "UPI/SYNC/TEST/002",
            "payment_screenshot_path": None,
            "recognition_type": "name_and_batch"
        }
    ]

    with patch("services.sync_service.get_alumnus_by_email", return_value=None), \
         patch("services.sync_service.create_alumnus", side_effect=[101, 102]) as mock_create_alumni, \
         patch("services.sync_service.save_meet_response") as mock_save_response, \
         patch("services.sync_service.create_contribution") as mock_create_contrib, \
         patch("services.sync_service.get_contribution_by_reference", return_value=None), \
         patch("services.sync_service.save_recognition_preference") as mock_save_recog, \
         patch("services.sync_service.log_audit_action"):

        result = perform_sync(meet_id=1, triggered_by="unit_test", records_override=mock_records)

        assert result["success"] is True
        assert result["metrics"]["total_rows"] == 2
        assert result["metrics"]["alumni_created"] == 2
        assert result["metrics"]["responses_synced"] == 2
        assert result["metrics"]["contributions_logged"] == 2
        assert mock_create_alumni.call_count == 2
        assert mock_save_response.call_count == 2
        assert mock_create_contrib.call_count == 2
        assert mock_save_recog.call_count == 2

def test_sync_api_endpoints(client):
    """Test sync API routes authentication and responses."""
    # Unauthorized access check
    res_status = client.get("/api/admin/sync/status")
    assert res_status.status_code == 401

    res_trigger = client.post("/api/admin/sync/trigger")
    assert res_trigger.status_code == 401

    # Authenticated session
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_email"] = "admin@scss.jnu.ac.in"
        sess["user_role"] = "organizer"

    # Status check
    res_status = client.get("/api/admin/sync/status")
    assert res_status.status_code == 200
    data = res_status.get_json()
    assert data["success"] is True
    assert "sync_state" in data
    assert "scheduler" in data

    # Trigger with mock
    with patch("routes.api.perform_sync", return_value={"success": True, "message": "Synced 5 records."}):
        res_trigger = client.post("/api/admin/sync/trigger")
        assert res_trigger.status_code == 200
        assert res_trigger.get_json()["success"] is True

def test_scheduler_info():
    """Test scheduler info output structure."""
    info = get_scheduler_info()
    assert "auto_sync_enabled" in info
    assert "interval_hours" in info
    assert info["interval_hours"] == 24
