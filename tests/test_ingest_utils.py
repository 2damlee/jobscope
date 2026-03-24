from pipeline.ingest_jobs import (
    clean_text,
    normalize_location,
    normalize_seniority,
    parse_date,
    is_valid_row,
)


def test_normalize_location():
    assert normalize_location("Berlin, Germany") == "Berlin"
    assert normalize_location("Berlin") == "Berlin"


def test_normalize_seniority():
    assert normalize_seniority("junior") == "Junior"
    assert normalize_seniority("Mid") == "Mid"


def test_parse_date_invalid():
    assert parse_date("not_a_date") is None


def test_is_valid_row():
    assert is_valid_row("Backend Engineer", "Python FastAPI PostgreSQL backend work", "https://x.com")[0] is True
    assert is_valid_row(None, "desc", "https://x.com")[0] is False
    assert is_valid_row("Title", "short", "https://x.com")[0] is False
    assert is_valid_row("Title", "Long enough description for validation", None)[0] is False