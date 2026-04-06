from datetime import date

from pipeline.state_utils import build_source_hash, has_source_changed
from pipeline.ingest_jobs import normalize_location, normalize_seniority


def test_build_source_hash_same_payload_same_hash():
    h1 = build_source_hash(
        title="Backend Engineer",
        company="Acme",
        location="Berlin",
        category="Software Engineering",
        seniority="Mid",
        description="Build backend services with Python and PostgreSQL.",
        date_posted=date(2026, 3, 10),
        url="https://example.com/jobs/1",
    )
    h2 = build_source_hash(
        title="Backend Engineer",
        company="Acme",
        location="Berlin",
        category="Software Engineering",
        seniority="Mid",
        description="Build backend services with Python and PostgreSQL.",
        date_posted=date(2026, 3, 10),
        url="https://example.com/jobs/1",
    )

    assert h1 == h2


def test_build_source_hash_changes_when_description_changes():
    h1 = build_source_hash(
        title="Backend Engineer",
        company="Acme",
        location="Berlin",
        category="Software Engineering",
        seniority="Mid",
        description="Build backend services.",
        date_posted=date(2026, 3, 10),
        url="https://example.com/jobs/1",
    )
    h2 = build_source_hash(
        title="Backend Engineer",
        company="Acme",
        location="Berlin",
        category="Software Engineering",
        seniority="Mid",
        description="Build scalable backend services.",
        date_posted=date(2026, 3, 10),
        url="https://example.com/jobs/1",
    )

    assert h1 != h2


def test_has_source_changed():
    assert has_source_changed("old_hash", "new_hash") is True
    assert has_source_changed("same_hash", "same_hash") is False
   
    
def test_normalize_seniority_variants_from_jobs_csv():
    assert normalize_seniority("junior") == "Junior"
    assert normalize_seniority("SENIOR") == "Senior"
    assert normalize_seniority("Mid") == "Mid"
    assert normalize_seniority("Senior") == "Senior"


def test_normalize_location_variants_from_jobs_csv():
    assert normalize_location("Berlin, Germany") == "Berlin"
    assert normalize_location("Munich, Germany") == "Munich"
    assert normalize_location("Frankfurt, Germany") == "Frankfurt"