import pytest
from datetime import datetime, timedelta
from backend.utils.helpers import (
    parse_date,
    calculate_years_to_maturity,
    format_number,
    rating_to_score,
    safe_float,
    safe_int,
    paginate_query
)

class TestHelpers:
    """
    Test suite for YieldLens backend utility helpers.
    """

    def test_parse_date_various_formats(self):
        assert isinstance(parse_date("2024-01-01"), datetime)
        assert isinstance(parse_date("01/01/2024"), datetime)
        assert isinstance(parse_date("2024-01-01T12:00:00"), datetime)
        
        with pytest.raises(ValueError):
            parse_date("invalid-date")

    def test_calculate_years_to_maturity(self):
        # 365.25 days from now
        future_date = datetime.utcnow() + timedelta(days=365.25)
        years = calculate_years_to_maturity(future_date)
        assert pytest.approx(years, rel=1e-2) == 1.0
        
        # Past date should return 0.01 (minimum)
        past_date = datetime.utcnow() - timedelta(days=100)
        assert calculate_years_to_maturity(past_date) == 0.01

    def test_format_number(self):
        assert format_number(10.1234, 2) == "10.12"
        assert format_number(10.1, 3) == "10.100"
        assert format_number("invalid") == "N/A"

    def test_rating_to_score(self):
        # Assuming AAA is 100 and D is low in constants.py
        assert rating_to_score("AAA") > rating_to_score("BBB")
        assert rating_to_score("BBB") > rating_to_score("C")
        # Default for unknown
        assert rating_to_score("UNKNOWN") == 50

    def test_safe_conversions(self):
        assert safe_float("10.5") == 10.5
        assert safe_float(None, 1.0) == 1.0
        assert safe_float("abc", 0.0) == 0.0
        
        assert safe_int("10") == 10
        assert safe_int(None, 5) == 5

    def test_paginate_query(self):
        skip, limit = paginate_query(page=1, limit=50)
        assert skip == 0
        assert limit == 50
        
        skip, limit = paginate_query(page=3, limit=20)
        assert skip == 40
        assert limit == 20
        
        # Min/Max constraints
        skip, limit = paginate_query(page=0, limit=500)
        assert skip == 0
        assert limit == 200
