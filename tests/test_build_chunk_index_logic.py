from types import SimpleNamespace

from pipeline.build_chunk_index import collect_chunk_records


def test_collect_chunk_records_builds_chunk_metadata():
    jobs = [
        SimpleNamespace(
            id=1,
            title="Backend Engineer",
            company="HelloFresh",
            location="Berlin",
            category="Software Engineering",
            seniority="Mid",
            cleaned_description="Build backend APIs. Work with FastAPI and PostgreSQL.",
            description="",
        )
    ]

    chunk_records, chunk_texts = collect_chunk_records(jobs)

    assert len(chunk_records) >= 1
    assert len(chunk_records) == len(chunk_texts)

    first = chunk_records[0]
    assert first["job_id"] == 1
    assert first["title"] == "Backend Engineer"
    assert "chunk_text" in first
    assert "chunk_length" in first
    assert first["chunk_length"] == len(first["chunk_text"])


def test_collect_chunk_records_uses_raw_description_when_cleaned_missing():
    jobs = [
        SimpleNamespace(
            id=2,
            title="Data Engineer",
            company="Zalando",
            location="Berlin",
            category="Data Engineering",
            seniority="Senior",
            cleaned_description=None,
            description="Build batch pipelines. Maintain SQL models and Airflow jobs.",
        )
    ]

    chunk_records, chunk_texts = collect_chunk_records(jobs)

    assert len(chunk_records) >= 1
    assert len(chunk_texts) >= 1
    assert all(record["job_id"] == 2 for record in chunk_records)


def test_collect_chunk_records_skips_jobs_without_text():
    jobs = [
        SimpleNamespace(
            id=3,
            title="Empty Job",
            company="Example",
            location="Berlin",
            category="Software Engineering",
            seniority="Junior",
            cleaned_description="",
            description="",
        )
    ]

    chunk_records, chunk_texts = collect_chunk_records(jobs)

    assert chunk_records == []
    assert chunk_texts == []