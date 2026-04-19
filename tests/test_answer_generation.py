from rag.answer_generation import detect_question_type, generate_answer


def test_detect_question_type():
    assert detect_question_type("Which backend jobs require FastAPI?") == "jobs"
    assert detect_question_type("What skills are common in analytics roles?") == "skills"
    assert detect_question_type("Tell me about backend roles") == "general"


def test_generate_answer_jobs():
    results = [
        {
            "job_id": 1,
            "title": "Backend Engineer",
            "location": "Berlin",
            "chunk_text": "Build backend APIs using Python and FastAPI. Work with PostgreSQL.",
        }
    ]

    answer, mode = generate_answer("Which backend jobs require FastAPI?", results)

    assert mode == "extractive"
    assert "Backend Engineer" in answer
    assert "FastAPI" in answer


def test_generate_answer_empty():
    answer, mode = generate_answer("Which backend jobs require FastAPI?", [])

    assert mode == "extractive"
    assert "No relevant" in answer