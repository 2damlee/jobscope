from pipeline.evaluate_rag import (
    evaluate_single_case,
    summarize_rag_results,
)


def test_evaluate_single_case_counts_keyword_hits(monkeypatch):
    def fake_answer_question(question):
        return {
            "answer": "This role requires Python, FastAPI, and SQL.",
            "results": [
                {"job_id": 1},
                {"job_id": 1},
                {"job_id": 2},
            ],
        }

    monkeypatch.setattr(
        "pipeline.evaluate_rag.answer_question",
        fake_answer_question,
    )

    case = {
        "question": "Which jobs mention Python and FastAPI?",
        "expected_keywords": ["Python", "FastAPI", "Docker"],
    }

    result = evaluate_single_case(case)

    assert result["matched_keywords"] == ["Python", "FastAPI"]
    assert result["keyword_hit_rate"] == 0.667
    assert result["retrieved_chunk_count"] == 3
    assert result["retrieved_job_count"] == 2


def test_summarize_rag_results_aggregates_case_metrics():
    results = [
        {
            "keyword_hit_rate": 1.0,
            "retrieved_chunk_count": 4,
            "retrieved_job_count": 2,
        },
        {
            "keyword_hit_rate": 0.5,
            "retrieved_chunk_count": 2,
            "retrieved_job_count": 1,
        },
    ]

    summary = summarize_rag_results(results)

    assert summary["total_cases"] == 2
    assert summary["passed_cases"] == 2
    assert summary["avg_keyword_hit_rate"] == 0.75
    assert summary["avg_retrieved_chunk_count"] == 3.0
    assert summary["avg_retrieved_job_count"] == 1.5