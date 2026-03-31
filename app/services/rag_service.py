from rag.qa import answer_question


def ask_question(
    question: str,
    category: str | None = None,
    location: str | None = None,
    seniority: str | None = None,
    top_k: int = 3,
):
    return answer_question(
        question=question,
        category=category,
        location=location,
        seniority=seniority,
        top_k=top_k,
    )