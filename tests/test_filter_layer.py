from rag.filters import apply_result_filters


def test_apply_result_filters_category():
    results = [
        {"job_id": 1, "category": "Backend", "location": "Berlin", "seniority": "Junior"},
        {"job_id": 2, "category": "ML", "location": "Munich", "seniority": "Mid"},
    ]

    filtered = apply_result_filters(results, category="Backend")
    assert len(filtered) == 1
    assert filtered[0]["job_id"] == 1


def test_apply_result_filters_multiple_fields():
    results = [
        {"job_id": 1, "category": "Backend", "location": "Berlin", "seniority": "Junior"},
        {"job_id": 2, "category": "Backend", "location": "Berlin", "seniority": "Senior"},
    ]

    filtered = apply_result_filters(results, category="Backend", location="Berlin", seniority="Junior")
    assert len(filtered) == 1
    assert filtered[0]["job_id"] == 1