from datetime import date

from pipeline.state_utils import build_source_hash, has_source_changed


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