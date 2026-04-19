import json

from app.config import PROCESSED_DIR, ensure_data_dirs
from app.time_utils import utcnow_naive
from rag.qa import answer_question

RAG_EVAL_CASES = [
    {
        "question": "Which backend jobs mention Python and FastAPI?",
        "expected_keywords": ["Python", "FastAPI"],
    },
    {
        "question": "Which jobs mention SQL and analytics?",
        "expected_keywords": ["SQL", "analytics"],
    },
]


def evaluate_single_case(case: dict) -> dict:
    question = case["question"]
    expected_keywords = case.get("expected_keywords", [])

    result = answer_question(question)
    answer = result.get("answer", "") if isinstance(result, dict) else str(result)
    retrieved_chunks = result.get("results", []) if isinstance(result, dict) else []

    matched_keywords = [
        keyword
        for keyword in expected_keywords
        if keyword.lower() in answer.lower()
    ]
    keyword_hit_rate = (
        round(len(matched_keywords) / len(expected_keywords), 3)
        if expected_keywords
        else 0.0
    )

    unique_job_ids = {
        item.get("job_id")
        for item in retrieved_chunks
        if item.get("job_id") is not None
    }

    return {
        "question": question,
        "expected_keywords": expected_keywords,
        "matched_keywords": matched_keywords,
        "keyword_hit_rate": keyword_hit_rate,
        "answer_length": len(answer),
        "retrieved_chunk_count": len(retrieved_chunks),
        "retrieved_job_count": len(unique_job_ids),
        "answer": answer,
    }


def summarize_rag_results(results: list[dict]) -> dict:
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r["keyword_hit_rate"] > 0)

    avg_keyword_hit_rate = (
        round(sum(r["keyword_hit_rate"] for r in results) / total_cases, 3)
        if total_cases
        else 0.0
    )
    avg_retrieved_chunk_count = (
        round(sum(r["retrieved_chunk_count"] for r in results) / total_cases, 3)
        if total_cases
        else 0.0
    )
    avg_retrieved_job_count = (
        round(sum(r["retrieved_job_count"] for r in results) / total_cases, 3)
        if total_cases
        else 0.0
    )

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "avg_keyword_hit_rate": avg_keyword_hit_rate,
        "avg_retrieved_chunk_count": avg_retrieved_chunk_count,
        "avg_retrieved_job_count": avg_retrieved_job_count,
    }


def save_rag_evaluation(summary: dict, results: list[dict]) -> str:
    ensure_data_dirs()
    output_path = PROCESSED_DIR / "rag_eval_results.json"

    payload = {
        "generated_at": utcnow_naive().isoformat(),
        "summary": summary,
        "cases": results,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return str(output_path)


def evaluate_rag() -> dict:
    results = [evaluate_single_case(case) for case in RAG_EVAL_CASES]
    summary = summarize_rag_results(results)
    output_path = save_rag_evaluation(summary, results)

    final_result = {
        "summary": summary,
        "output_path": output_path,
    }
    print(json.dumps(final_result, ensure_ascii=False, indent=2))
    return final_result


if __name__ == "__main__":
    evaluate_rag()