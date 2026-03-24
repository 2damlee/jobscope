from rag.retriever import search_chunks
from rag.answer_generation import generate_answer


def rerank_results(results, question):
    reranked = []

    for r in results:
        final_score = 0.8 * r["score"] + 0.2 * r["keyword_score"]
        item = dict(r)
        item["final_score"] = round(float(final_score), 4)
        reranked.append(item)

    reranked.sort(key=lambda x: x["final_score"], reverse=True)
    return reranked


def deduplicate_by_job(results, max_chunks_per_job=2):
    grouped = {}
    deduped = []

    for r in results:
        job_id = r["job_id"]
        grouped.setdefault(job_id, 0)

        if grouped[job_id] >= max_chunks_per_job:
            continue

        deduped.append(r)
        grouped[job_id] += 1

    return deduped


def answer_question(
    question: str,
    category: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    top_k: int = 5,
):
    top_k = max(1, top_k)

    raw_results = search_chunks(question, top_k=top_k * 4)

    filtered = []
    for r in raw_results:
        if category and (r["category"] or "").lower() != category.lower():
            continue
        if location and (r["location"] or "").lower() != location.lower():
            continue
        if seniority and (r["seniority"] or "").lower() != seniority.lower():
            continue
        filtered.append(r)

    reranked = rerank_results(filtered, question)
    deduped = deduplicate_by_job(reranked, max_chunks_per_job=1)
    final_results = deduped[:top_k]

    matched_chunks = [r["chunk_text"] for r in final_results]
    answer, generation_mode = generate_answer(question, final_results)

    sources = []
    for r in final_results:
        sources.append({
            "job_id": r["job_id"],
            "title": r["title"],
            "company": r["company"],
            "location": r["location"],
            "category": r["category"],
            "seniority": r["seniority"],
            "chunk_id": r["chunk_id"],
            "score": r["final_score"],
        })

    return {
        "answer": answer,
        "generation_mode": generation_mode,
        "sources": sources,
        "matched_chunks": matched_chunks,
    }