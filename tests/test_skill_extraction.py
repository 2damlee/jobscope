from pipeline.extract_skills import extract_skills


def test_extract_basic_skills():
    text = "Build backend APIs using Python, FastAPI, PostgreSQL, and Docker."
    skills = extract_skills(text)
    assert "python" in skills
    assert "fastapi" in skills
    assert "postgresql" in skills
    assert "docker" in skills
    assert "api" in skills


def test_extract_aliases():
    text = "Experience with postgres, sklearn, and amazon web services is preferred."
    skills = extract_skills(text)
    assert "postgresql" in skills
    assert "scikit-learn" in skills
    assert "aws" in skills


def test_extract_nlp_and_embeddings():
    text = "Work on NLP pipelines, embeddings, transformers, and semantic search."
    skills = extract_skills(text)
    assert "nlp" in skills
    assert "embeddings" in skills
    assert "transformers" in skills
    assert "vector-search" in skills


def test_extract_empty_text():
    assert extract_skills("") == []