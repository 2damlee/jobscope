import pytest
from fastapi import HTTPException

from app.services import rag_service


def test_ask_question_normalizes_inputs(monkeypatch):
    captured = {}

    def fake_answer_question(question, category=None, location=None, seniority=None, top_k=3):
        captured["question"] = question
        captured["category"] = category
        captured["location"] = location
        captured["seniority"] = seniority
        captured["top_k"] = top_k
        return {"answer": "ok"}

    monkeypatch.setattr(rag_service, "answer_question", fake_answer_question)

    result = rag_service.ask_question(
        question="  Which backend jobs require FastAPI?  ",
        category="  Backend  ",
        location="  Berlin  ",
        seniority="  Senior  ",
        top_k=5,
    )

    assert result == {"answer": "ok"}
    assert captured == {
        "question": "Which backend jobs require FastAPI?",
        "category": "backend",
        "location": "Berlin",
        "seniority": "senior",
        "top_k": 5,
    }


def test_ask_question_raises_for_blank_question():
    with pytest.raises(HTTPException) as exc:
        rag_service.ask_question("   ")

    assert exc.value.status_code == 422
    assert exc.value.detail == "Question cannot be empty"