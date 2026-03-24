from rag.qa import deduplicate_by_job, rerank_results


def test_deduplicate_by_job():
    results = [
        {"job_id": 1, "score": 0.9, "keyword_score": 0.5, "chunk_text": "a", "title": "A"},
        {"job_id": 1, "score": 0.8, "keyword_score": 0.4, "chunk_text": "b", "title": "A"},
        {"job_id": 2, "score": 0.7, "keyword_score": 0.3, "chunk_text": "c", "title": "B"},
    ]

    deduped = deduplicate_by_job(results, max_chunks_per_job=1)
    assert len(deduped) == 2


def test_rerank_results():
    results = [
        {"job_id": 1, "score": 0.7, "keyword_score": 0.1, "chunk_text": "a", "title": "A"},
        {"job_id": 2, "score": 0.6, "keyword_score": 0.8, "chunk_text": "b", "title": "B"},
    ]

    reranked = rerank_results(results, "backend fastapi")
    assert reranked[0]["job_id"] == 2