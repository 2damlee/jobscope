from rag.qa import answer_question
from tests.rag_eval_cases import RAG_EVAL_CASES


def evaluate():
    for i, case in enumerate(RAG_EVAL_CASES, start=1):
        result = answer_question(
            question=case["question"],
            category=case["filters"].get("category"),
            location=case["filters"].get("location"),
            seniority=case["filters"].get("seniority"),
            top_k=3,
        )

        text_blob = " ".join(result["matched_chunks"]).lower()
        matched = [kw for kw in case["expected_keywords"] if kw in text_blob]

        print("=" * 80)
        print(f"Case {i}")
        print("Question:", case["question"])
        print("Matched expected keywords:", matched)
        print("Sources:", [s["title"] for s in result["sources"]])
        print("Answer:", result["answer"])
        print()