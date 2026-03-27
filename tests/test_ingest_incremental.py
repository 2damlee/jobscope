from datetime import date
import pandas as pd
from pipeline.state_utils import build_source_hash


def test_source_hash_is_stable_for_same_payload():
    payload = {
        "title": "Data Engineer",
        "company": "Acme",
        "location": "Berlin",
        "category": "Data Engineering",
        "seniority": "Mid",
        "description": "Build reliable pipelines.",
        "date_posted": date(2026, 3, 1),
        "url": "https://example.com/jobs/2",
    }

    first = build_source_hash(**payload)
    second = build_source_hash(**payload)

    assert first == second


def test_source_hash_changes_when_title_changes():
    first = build_source_hash(
        title="Data Engineer",
        company="Acme",
        location="Berlin",
        category="Data Engineering",
        seniority="Mid",
        description="Build reliable pipelines.",
        date_posted=date(2026, 3, 1),
        url="https://example.com/jobs/2",
    )
    second = build_source_hash(
        title="Senior Data Engineer",
        company="Acme",
        location="Berlin",
        category="Data Engineering",
        seniority="Mid",
        description="Build reliable pipelines.",
        date_posted=date(2026, 3, 1),
        url="https://example.com/jobs/2",
    )

    assert first != second
    
def test_dedupe_rows_by_url_keeps_last_duplicate():
    df = pd.DataFrame(
        [
            {
                "title": "Data Engineer",
                "company": "A",
                "location": "Berlin, Germany",
                "category": "Data Engineering",
                "seniority": "Senior",
                "description": "A" * 40,
                "date_posted": "2026-03-08",
                "url": "https://example.com/jobs/berlin-data-engineer-002",
            },
            {
                "title": "Data Engineer",
                "company": "B",
                "location": "Berlin, Germany",
                "category": "Data Engineering",
                "seniority": "Senior",
                "description": "B" * 50,
                "date_posted": "2026-03-20",
                "url": "https://example.com/jobs/berlin-data-engineer-002",
            },
        ]
    )

    prepared_rows, skipped, skip_reasons, duplicate_urls_in_file = dedupe_rows_by_url(df)

    assert skipped == 0
    assert duplicate_urls_in_file == 1
    assert len(prepared_rows) == 1
    assert prepared_rows[0]["company"] == "B"
    assert prepared_rows[0]["description"] == "B" * 50