from rag.answer_generation import generate_extractive_answer, detect_question_type


def test_detect_question_type_skills():
    assert detect_question_type("What skills are common in analytics roles?") == "skills"


def test_generate_extractive_answer_jobs():
    results = [
        {
            "job_id": 1,
            "title": "Backend Engineer",
            "location": "Berlin",
            "chunk_text": "Build backend APIs using Python and FastAPI. Work with PostgreSQL."
        }
    ]

    answer = generate_extractive_answer("Which backend jobs require FastAPI?", results)
    assert "Backend Engineer" in answer


def test_generate_extractive_answer_empty():
    answer = generate_extractive_answer("Which backend jobs require FastAPI?", [])
    assert "No relevant" in answer