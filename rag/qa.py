from rag.retriever import search_chunks


def answer_question(
    question: str,
    category: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    top_k: int = 5,
):
    top_k = max(1, top_k)

    results = search_chunks(question, top_k=top_k * 2)

    filtered = []
    for r in results:
        if category and (r["category"] or "").lower() != category.lower():
            continue
        if location and (r["location"] or "").lower() != location.lower():
            continue
        if seniority and (r["seniority"] or "").lower() != seniority.lower():
            continue
        filtered.append(r)

    filtered = filtered[:top_k]

    if not filtered:
        return {
            "answer": "No relevant job posting information was found for the given question and filters.",
            "sources": [],
            "matched_chunks": [],
        }

    matched_chunks = [r["chunk_text"] for r in filtered]

    answer = "Based on the retrieved job postings, the most relevant requirements and responsibilities are:\n\n"
    for i, chunk in enumerate(matched_chunks, start=1):
        answer += f"{i}. {chunk}\n"

    sources = []
    for r in filtered:
        sources.append({
            "job_id": r["job_id"],
            "title": r["title"],
            "company": r["company"],
            "location": r["location"],
            "category": r["category"],
            "seniority": r["seniority"],
            "chunk_id": r["chunk_id"],
            "score": r["score"],
        })

    return {
        "answer": answer.strip(),
        "sources": sources,
        "matched_chunks": matched_chunks,
    }