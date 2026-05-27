"""
YieldLens Helper Utilities
Common helper functions used throughout the application.
"""

from datetime import date, datetime

from flask import Response, jsonify
from utils.constants import RATING_SCORES


def to_object_id(id_str: str):
    """
    Convert a string to a MongoDB ObjectId if possible.
    
    Args:
        id_str: The string to convert.
        
    Returns:
        An ObjectId or the original string if conversion fails.
    """
    try:
        from bson import ObjectId
        return ObjectId(id_str)
    except Exception:
        return id_str


def json_response(
    data: dict | list | str, status: int = 200, success: bool = True
) -> tuple[Response, int]:
    """
    Build a consistent JSON response envelope.

    Args:
        data: The payload to return.
        status: HTTP status code (default 200).
        success: Whether the operation succeeded.

    Returns:
        A tuple of (Flask Response, status code).
    """
    body = {
        "success": success,
        "data": data,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    if not success:
        body = {
            "success": False,
            "error": data if isinstance(data, str) else str(data),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    return jsonify(body), status


def error_response(message: str, status: int = 400) -> tuple[Response, int]:
    """Return a standardised error response."""
    return json_response(message, status=status, success=False)


def parse_date(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object.
    Supports formats: YYYY-MM-DD, MM/DD/YYYY, YYYY-MM-DDTHH:MM:SS.

    Args:
        date_str: The date string to parse.

    Returns:
        A datetime object.

    Raises:
        ValueError: If the date string cannot be parsed.
    """
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")


def calculate_years_to_maturity(maturity_date: str | datetime | date) -> float:
    """
    Calculate the number of years between now and a maturity date.

    Args:
        maturity_date: The bond maturity date (string or datetime).

    Returns:
        Years to maturity as a float (minimum 0.01).
    """
    if isinstance(maturity_date, str):
        maturity_dt = parse_date(maturity_date)
    elif isinstance(maturity_date, date) and not isinstance(maturity_date, datetime):
        maturity_dt = datetime.combine(maturity_date, datetime.min.time())
    else:
        maturity_dt = maturity_date

    today = datetime.utcnow()
    delta = maturity_dt - today
    years = delta.days / 365.25
    return max(years, 0.01)


def format_number(n: float | int, decimals: int = 2) -> str:
    """
    Format a number to a fixed number of decimal places.

    Args:
        n: The number to format.
        decimals: Decimal places (default 2).

    Returns:
        Formatted string.
    """
    try:
        return f"{float(n):.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def rating_to_score(rating: str) -> int:
    """
    Convert a credit rating string to a numerical score (0-100).

    Args:
        rating: Standard credit rating (e.g. 'AAA', 'BB+').

    Returns:
        Integer score from 0 (D) to 100 (AAA).
    """
    return RATING_SCORES.get(rating.upper().strip(), 50)


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default on failure."""
    try:
        v = float(value)
        if v != v:  # NaN check
            return default
        return v
    except (TypeError, ValueError):
        return default


def safe_int(value, default: int = 0) -> int:
    """Safely convert a value to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def paginate_query(page: int = 1, limit: int = 50) -> tuple[int, int]:
    """
    Calculate skip and limit for pagination.

    Args:
        page: Page number (1-indexed).
        limit: Items per page.

    Returns:
        Tuple of (skip, limit).
    """
    page = max(1, page)
    limit = max(1, min(200, limit))
    skip = (page - 1) * limit
    return skip, limit
