import pytest
from unittest.mock import patch
from services.alumni_service import get_public_alumni_directory

def test_public_alumni_directory_privacy_projection():
    """Verify that public alumni projection never leaks email, phone, or payment data."""
    mock_db_alumni = [
        {
            "id": 1,
            "full_name": "Alumnus One",
            "graduation_year": 2012,
            "course": "MCA",
            "organization": "Tech Corp",
            "designation": "Staff Engineer",
            "current_location": "Bengaluru",
            "recognition_type": "name_and_organization"
        },
        {
            "id": 2,
            "full_name": "Alumnus Two",
            "graduation_year": 2018,
            "course": "M.Tech",
            "organization": "Private Bank",
            "designation": "Analyst",
            "current_location": "Delhi",
            "recognition_type": "name_only"
        },
        {
            "id": 3,
            "full_name": "Alumnus Three",
            "graduation_year": 2020,
            "course": "Ph.D.",
            "organization": "Research Lab",
            "designation": "Scientist",
            "current_location": "Zurich",
            "recognition_type": "anonymous"
        }
    ]

    with patch("services.alumni_service.get_public_alumni_list", return_value=mock_db_alumni):
        directory = get_public_alumni_directory()

        assert len(directory) == 3

        # Record 1: name_and_organization
        p1 = directory[0]
        assert p1["full_name"] == "Alumnus One"
        assert p1["organization"] == "Tech Corp"
        assert "email" not in p1
        assert "phone" not in p1
        assert "transaction_reference" not in p1

        # Record 2: name_only (Organization should be hidden)
        p2 = directory[1]
        assert p2["full_name"] == "Alumnus Two"
        assert p2["organization"] is None
        assert p2["designation"] is None
        assert "email" not in p2

        # Record 3: anonymous (Name should be masked)
        p3 = directory[2]
        assert "Anonymous" in p3["full_name"]
        assert p3["organization"] is None
        assert p3["designation"] is None
