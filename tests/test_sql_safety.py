import pytest
from unittest.mock import patch, MagicMock
import db.alumni as alumni_db
import db.contributions as contrib_db
import db.volunteers as vol_db
import db.activities as act_db
import db.users as users_db
import db.audit as audit_db

def test_alumni_db_parameterized_queries():
    """Verify that alumni DB functions execute parameterized SQL queries without syntax flaws."""
    with patch("db.alumni.execute_query") as mock_exec:
        mock_exec.return_value = []
        
        # Test public alumni query with filters
        alumni_db.get_public_alumni_list(
            meet_id=1,
            search="Sharma",
            graduation_year=2015,
            course="MCA"
        )
        assert mock_exec.called
        sql, params = mock_exec.call_args[0]
        assert "a.full_name" in sql
        # Ensure parameterized %s placeholders are used
        assert "%s" in sql
        assert 1 in params
        assert "%Sharma%" in params
        assert 2015 in params
        assert "MCA" in params

def test_contribution_db_queries():
    """Verify contribution queries use correct parameters."""
    with patch("db.contributions.execute_query") as mock_exec:
        mock_exec.return_value = []
        contrib_db.get_contributions_admin(
            meet_id=1,
            status="verified",
            search="Amit"
        )
        assert mock_exec.called
        sql, params = mock_exec.call_args[0]
        assert "%s" in sql
        assert "verified" in params
        assert "%Amit%" in params

def test_volunteer_db_queries():
    """Verify volunteer queries operate independently of alumni table."""
    with patch("db.volunteers.execute_query") as mock_exec:
        mock_exec.return_value = []
        vol_db.get_all_volunteers(status="active", search="Host")
        assert mock_exec.called
        sql, params = mock_exec.call_args[0]
        assert "FROM volunteers" in sql
        assert "JOIN alumni" not in sql  # Volunteer entity MUST be independent of alumni
        assert "active" in params
        assert "%Host%" in params
