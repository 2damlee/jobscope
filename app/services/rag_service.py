from fastapi import HTTPException

from rag.qa import answer_question


def ask_question(
    question: str,
    category: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    top_k: int = 3,
):
    question = question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be empty")

    normalized_category = category.strip().lower() if category else None
    normalized_location = location.strip() if location else None
    normalized_seniority = seniority.strip().lower() if seniority else None

    return answer_question(
        question=question,
        category=normalized_category,
        location=normalized_location,
        seniority=normalized_seniority,
        top_k=top_k,
    )