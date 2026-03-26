from datetime import date

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